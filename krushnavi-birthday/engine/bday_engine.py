"""
bday_engine.py - shared rendering engine for Krushnavi's birthday status videos.

Design rules baked in:
  * Photos are NEVER generated or altered by AI - only cropped, scaled, framed, masked, graded.
  * fit() is face-safe: every crop keeps Krushnavi's face box (and optionally other faces) inside the frame.
  * Output: 1080x1920 (9:16), 30 fps, H.264 yuv420p + AAC, faststart (WhatsApp / Instagram status friendly).

Main API (see docstrings):
  photo(i), meta(i), fit(i, w, h, zoom, pan, focus, keep, y_bias), kenburns(...), blur_bg(i, ...)
  font(name, size, variation), text_layer(...), blit(frame, layer, cx, cy, scale, alpha, rot)
  rounded_mask / circle_mask / heart_mask / apply_mask / framed / polaroid / shadow / panel / vgradient
  Particles(kind, ...).draw(frame, t)   kinds: confetti, balloon, sparkle, bokeh, heart, petal, star, streamer
  Timeline().add(dur, render_fn, trans='fade', tdur=0.6) ; timeline.overlays.append(fn(frame, t))
  encode(timeline, out_mp4, audio=None, workers=3) ; preview(timeline, out_jpg, n=12) ; snap(timeline, t, out)
"""
import os, math, json, subprocess, shutil, tempfile, multiprocessing as mp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, 'assets')
PHOTO_DIR = os.path.join(ASSETS, 'photos')
FONT_DIR = os.path.join(ROOT, 'fonts')
AUDIO_DIR = os.path.join(ASSETS, 'audio')
W, H, FPS = 1080, 1920, 30

# ----------------------------------------------------------------------------- math / easing
def clamp(v, lo=0.0, hi=1.0): return lo if v < lo else hi if v > hi else v
def clamp01(v): return clamp(v, 0.0, 1.0)
def lerp(a, b, t): return a + (b - a) * t
def seg(t, t0, t1):
    """progress 0..1 of t inside [t0, t1] (clamped)."""
    if t1 <= t0: return 1.0 if t >= t1 else 0.0
    return clamp01((t - t0) / (t1 - t0))
def ease_linear(t): return t
def ease_in_out(t): return t * t * (3 - 2 * t)                      # smoothstep
def ease_in_out_sine(t): return -(math.cos(math.pi * t) - 1) / 2
def ease_out_cubic(t): return 1 - (1 - t) ** 3
def ease_in_cubic(t): return t ** 3
def ease_in_out_cubic(t): return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def ease_out_quint(t): return 1 - (1 - t) ** 5
def ease_out_back(t, s=1.70158): return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2
def ease_out_elastic(t):
    if t <= 0: return 0.0
    if t >= 1: return 1.0
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1
def ease_out_bounce(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1: return n1 * t * t
    if t < 2 / d1: t -= 1.5 / d1; return n1 * t * t + .75
    if t < 2.5 / d1: t -= 2.25 / d1; return n1 * t * t + .9375
    t -= 2.625 / d1; return n1 * t * t + .984375
def pulse(t, period=1.0, lo=0.0, hi=1.0):
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(2 * math.pi * t / period))
def stagger(u, i, n, overlap=0.5):
    """progress of element i of n when total progress is u; each element takes (1/n)/(1-overlap*(n-1)/n) of the time."""
    if n <= 1: return clamp01(u)
    span = 1.0 / (1 + (n - 1) * (1 - overlap))
    start = i * span * (1 - overlap)
    return clamp01((u - start) / span)

def hexc(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
def with_alpha(c, a):
    return (c[0], c[1], c[2], int(a))

# ----------------------------------------------------------------------------- photos & metadata
_PHOTOS = None
def photos_meta():
    global _PHOTOS
    if _PHOTOS is None:
        with open(os.path.join(ASSETS, 'photos.json')) as f:
            _PHOTOS = json.load(f)
    return _PHOTOS
def key(i): return i if isinstance(i, str) else f'p{i:02d}'
def meta(i): return photos_meta()[key(i)]
def all_ids(): return sorted(photos_meta().keys())

_IMG = {}
def photo(i, grade=None):
    """Full working-resolution RGB photo (1620x2160). grade=(brightness, contrast, color/saturation) optional."""
    k = (key(i), grade)
    if k not in _IMG:
        if grade is None:
            im = Image.open(os.path.join(PHOTO_DIR, key(i) + '.jpg')).convert('RGB')
        else:
            im = photo(i)
            b, c, s = grade
            if b != 1: im = ImageEnhance.Brightness(im).enhance(b)
            if c != 1: im = ImageEnhance.Contrast(im).enhance(c)
            if s != 1: im = ImageEnhance.Color(im).enhance(s)
        _IMG[k] = im
    return _IMG[k]

def faces(i, which='all'):
    m = meta(i)
    if which == 'girl': return [m['girl']]
    return [m['girl']] + list(m.get('others', []))

def focus_point(i, mode='girl'):
    """normalized (x, y) focus for a photo: 'girl' = centre of her face, 'all' = centre of all faces, 'body' = centre of her body box."""
    m = meta(i)
    if isinstance(mode, (tuple, list)): return tuple(mode)
    if mode == 'body':
        b = m.get('body', m['girl']); return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    boxes = [m['girl']] + (list(m.get('others', [])) if mode == 'all' else [])
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
    return ((x0 + x1) / 2, (y0 + y1) / 2)

def cover_box(img, tw, th, focus=(0.5, 0.4), zoom=1.0, pan=(0, 0), keep=None, margin=0.05):
    """Crop box (source px, floats) with aspect tw:th that covers the target. zoom>=1 zooms in.
    focus = normalized point placed at the centre (then shifted by pan, in crop-size units).
    keep = list of normalized boxes that must stay fully inside the crop (shifts the crop if needed)."""
    sw, sh = img.size
    zoom = max(1.0, zoom)
    if sw / sh > tw / th:
        ch = sh; cw = sh * tw / th
    else:
        cw = sw; ch = sw * th / tw
    cw /= zoom; ch /= zoom
    cx = focus[0] * sw + pan[0] * cw; cy = focus[1] * sh + pan[1] * ch
    x0 = cx - cw / 2; y0 = cy - ch / 2
    if keep:
        kx0 = min(b[0] for b in keep) * sw; ky0 = min(b[1] for b in keep) * sh
        kx1 = max(b[2] for b in keep) * sw; ky1 = max(b[3] for b in keep) * sh
        mx = margin * cw; my = margin * ch
        # if the keep-region is wider/taller than the crop, centre on it (girl box is first -> prioritise)
        if kx1 - kx0 + 2 * mx > cw: g = keep[0]; kx0 = g[0] * sw; kx1 = g[2] * sw
        if ky1 - ky0 + 2 * my > ch: g = keep[0]; ky0 = g[1] * sh; ky1 = g[3] * sh
        if x0 > kx0 - mx: x0 = kx0 - mx
        if x0 + cw < kx1 + mx: x0 = kx1 + mx - cw
        if y0 > ky0 - my: y0 = ky0 - my
        if y0 + ch < ky1 + my: y0 = ky1 + my - ch
    x0 = max(0.0, min(sw - cw, x0)); y0 = max(0.0, min(sh - ch, y0))
    return (x0, y0, x0 + cw, y0 + ch)

def fit(i, tw, th, zoom=1.0, pan=(0, 0), focus='girl', keep='auto', y_bias=0.0, grade=None, img=None):
    """Face-safe cover crop of photo i rendered at (tw, th).
    focus: 'girl' | 'all' | 'body' | (x, y) normalized.  keep: 'auto' | 'girl' | 'all' | None | list of boxes.
    y_bias shifts the focus point vertically (normalized source units, + = down -> shows more body)."""
    img = img if img is not None else photo(i, grade)
    fp = focus_point(i, focus)
    fp = (fp[0], fp[1] + y_bias)
    if keep == 'auto': keep = faces(i, 'all') if zoom <= 1.3 else faces(i, 'girl')
    elif keep == 'girl': keep = faces(i, 'girl')
    elif keep == 'all': keep = faces(i, 'all')
    box = cover_box(img, tw, th, fp, zoom, pan, keep)
    return img.resize((int(tw), int(th)), Image.LANCZOS, box=box, reducing_gap=3.0)

def kenburns(i, tw, th, u, z0=1.0, z1=1.12, p0=(0, 0), p1=(0, 0), ease=ease_in_out_sine, **kw):
    """Ken Burns: u in 0..1 -> zoom z0->z1 and pan p0->p1 (face safe)."""
    e = ease(clamp01(u))
    return fit(i, tw, th, zoom=lerp(z0, z1, e), pan=(lerp(p0[0], p1[0], e), lerp(p0[1], p1[1], e)), **kw)

_BG = {}
def blur_bg(i, tw=W, th=H, blur=28, dark=0.55, sat=1.1, tint=None):
    """Blurred, darkened cover of the same photo - the classic 'portrait on 9:16' background. Cached."""
    k = (key(i), tw, th, blur, dark, sat, tint)
    if k not in _BG:
        small = fit(i, tw // 4, th // 4, zoom=1.0, focus='all', keep=None)
        small = small.filter(ImageFilter.GaussianBlur(blur / 4))
        small = ImageEnhance.Brightness(small).enhance(dark)
        if sat != 1: small = ImageEnhance.Color(small).enhance(sat)
        bg = small.resize((tw, th), Image.BILINEAR).convert('RGBA')
        if tint:
            bg = Image.alpha_composite(bg, Image.new('RGBA', (tw, th), tint))
        _BG[k] = bg
    return _BG[k]

def contain(i, tw, th, grade=None):
    """Whole photo (no crop) scaled to fit inside tw x th. Returns RGB of the scaled size."""
    img = photo(i, grade); sw, sh = img.size
    s = min(tw / sw, th / sh)
    return img.resize((max(1, int(sw * s)), max(1, int(sh * s))), Image.LANCZOS, reducing_gap=3.0)

# ----------------------------------------------------------------------------- frames, masks, shapes
def new_frame(color=(0, 0, 0, 255)):
    return Image.new('RGBA', (W, H), color)

def rgba(img):
    return img if img.mode == 'RGBA' else img.convert('RGBA')

_MASKS = {}
def rounded_mask(w, h, r):
    k = ('r', w, h, r)
    if k not in _MASKS:
        m = Image.new('L', (w * 2, h * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=r * 2, fill=255)
        _MASKS[k] = m.resize((w, h), Image.LANCZOS)
    return _MASKS[k]
def circle_mask(w, h=None):
    h = h or w
    k = ('c', w, h)
    if k not in _MASKS:
        m = Image.new('L', (w * 2, h * 2), 0)
        ImageDraw.Draw(m).ellipse((0, 0, w * 2 - 1, h * 2 - 1), fill=255)
        _MASKS[k] = m.resize((w, h), Image.LANCZOS)
    return _MASKS[k]
def heart_points(w, h, n=120):
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((w / 2 + x / 34 * w, h / 2 - y / 34 * h + 0.04 * h))
    return pts
def heart_mask(w, h=None):
    h = h or w
    k = ('h', w, h)
    if k not in _MASKS:
        m = Image.new('L', (w * 2, h * 2), 0)
        ImageDraw.Draw(m).polygon(heart_points(w * 2, h * 2), fill=255)
        _MASKS[k] = m.resize((w, h), Image.LANCZOS)
    return _MASKS[k]
def star_points(cx, cy, r, n=5, inner=0.45, rot=-90):
    pts = []
    for k in range(2 * n):
        rr = r if k % 2 == 0 else r * inner
        a = math.radians(rot + 180 / n * k)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts

def apply_mask(img, mask):
    out = rgba(img).copy()
    out.putalpha(ImageChops.multiply(out.getchannel('A'), mask))
    return out

def shadow(layer, offset=(0, 18), blur=22, opacity=0.55, color=(0, 0, 0), pad=None):
    """Return a new RGBA layer = soft drop shadow + the layer, padded so nothing clips."""
    pad = pad if pad is not None else int(blur * 2 + max(abs(offset[0]), abs(offset[1])) + 4)
    w, h = layer.size
    out = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    a = layer.getchannel('A').point(lambda v: int(v * opacity))
    sh.paste(Image.new('RGBA', layer.size, color + (255,)), (pad + offset[0], pad + offset[1]), a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.alpha_composite(out, sh)
    out.alpha_composite(layer, (pad, pad))
    return out

def framed(img, border=22, color=(255, 255, 255, 255), radius=0, shadow_on=True, shadow_kw=None):
    """White (or coloured) border frame around an image, optional rounded corners and drop shadow."""
    img = rgba(img); w, h = img.size
    fw, fh = w + 2 * border, h + 2 * border
    base = Image.new('RGBA', (fw, fh), color)
    base.alpha_composite(img, (border, border))
    if radius: base = apply_mask(base, rounded_mask(fw, fh, radius))
    return shadow(base, **(shadow_kw or {})) if shadow_on else base

def panel(w, h, radius=40, fill=(0, 0, 0, 110), outline=None, width=3):
    p = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(p).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=fill, outline=outline, width=width)
    return p

def vgradient(w, h, colors, y0=0, y1=None, alpha=None):
    """Vertical gradient RGBA image through a list of colours (RGB/RGBA tuples)."""
    y1 = h if y1 is None else y1
    cols = [c if len(c) == 4 else tuple(c) + (255,) for c in colors]
    ys = np.clip((np.arange(h) - y0) / max(1, (y1 - y0)), 0, 1)
    n = len(cols) - 1
    pos = ys * n; idx = np.minimum(pos.astype(int), n - 1); f = pos - idx
    c0 = np.array([cols[k] for k in idx], dtype=float); c1 = np.array([cols[min(k + 1, n)] for k in idx], dtype=float)
    col = c0 + (c1 - c0) * f[:, None]
    arr = np.repeat(col[:, None, :], w, axis=1).astype(np.uint8)
    if alpha is not None: arr[:, :, 3] = alpha
    return Image.fromarray(arr, 'RGBA')

def hgradient(w, h, colors):
    return vgradient(h, w, colors).rotate(-90, expand=True)

def radial_sprite(size, color, inner=0.0, power=1.6):
    """Soft radial glow sprite (RGBA)."""
    y, x = np.mgrid[0:size, 0:size]
    r = np.sqrt((x - size / 2 + .5) ** 2 + (y - size / 2 + .5) ** 2) / (size / 2)
    a = np.clip(1 - (r - inner) / max(1e-6, 1 - inner), 0, 1) ** power
    arr = np.zeros((size, size, 4), np.uint8)
    arr[:, :, 0] = color[0]; arr[:, :, 1] = color[1]; arr[:, :, 2] = color[2]
    arr[:, :, 3] = (a * (color[3] if len(color) > 3 else 255)).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

_VIG = {}
def vignette(strength=0.55, size=(W, H), power=2.2):
    k = (strength, size, power)
    if k not in _VIG:
        w, h = size
        y, x = np.mgrid[0:h, 0:w]
        r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2) / math.sqrt(2)
        a = np.clip(r, 0, 1) ** power * strength
        arr = np.zeros((h, w, 4), np.uint8); arr[:, :, 3] = (a * 255).astype(np.uint8)
        _VIG[k] = Image.fromarray(arr, 'RGBA')
    return _VIG[k]

# ----------------------------------------------------------------------------- text
_FONTS = {}
def font(name, size, variation=None):
    """name = file in fonts/ (e.g. 'Pacifico-Regular.ttf', 'Poppins-Bold.ttf', 'DancingScript[wght].ttf').
    variation = named instance for variable fonts ('Bold', 'SemiBold', ...)."""
    k = (name, int(size), variation)
    if k not in _FONTS:
        p = name if os.path.isabs(name) else os.path.join(FONT_DIR, name)
        f = ImageFont.truetype(p, int(size))
        if variation:
            try: f.set_variation_by_name(variation)
            except Exception: pass
        _FONTS[k] = f
    return _FONTS[k]

def text_layer(text, fnt, fill=(255, 255, 255, 255), stroke=0, stroke_fill=(0, 0, 0, 255),
               shadow_c=None, shadow_off=(0, 10), shadow_blur=14,
               glow=None, glow_radius=24, glow_strength=1.6,
               gradient=None, align='center', spacing=8, pad=None):
    """Render text to a tight RGBA layer with optional glow, drop shadow, stroke and vertical gradient fill."""
    tmp = Image.new('L', (4, 4)); d = ImageDraw.Draw(tmp)
    bbox = d.multiline_textbbox((0, 0), text, font=fnt, stroke_width=stroke, align=align, spacing=spacing)
    tw, th = int(math.ceil(bbox[2] - bbox[0])), int(math.ceil(bbox[3] - bbox[1]))
    if pad is None:
        pad = int(max(glow_radius * 2 if glow else 0,
                      (shadow_blur * 2 + abs(shadow_off[0]) + abs(shadow_off[1])) if shadow_c else 0, stroke) + 8)
    Wl, Hl = int(tw + 2 * pad), int(th + 2 * pad)
    ox, oy = pad - bbox[0], pad - bbox[1]
    out = Image.new('RGBA', (Wl, Hl), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', (Wl, Hl), (0, 0, 0, 0))
        ImageDraw.Draw(g).multiline_text((ox, oy), text, font=fnt, fill=glow, align=align, spacing=spacing,
                                         stroke_width=stroke + 3, stroke_fill=glow)
        g = g.filter(ImageFilter.GaussianBlur(glow_radius))
        g.putalpha(g.getchannel('A').point(lambda v: min(255, int(v * glow_strength))))
        out = Image.alpha_composite(out, g)
    if shadow_c:
        s = Image.new('RGBA', (Wl, Hl), (0, 0, 0, 0))
        ImageDraw.Draw(s).multiline_text((ox + shadow_off[0], oy + shadow_off[1]), text, font=fnt, fill=shadow_c,
                                         align=align, spacing=spacing, stroke_width=stroke, stroke_fill=shadow_c)
        if shadow_blur: s = s.filter(ImageFilter.GaussianBlur(shadow_blur))
        out = Image.alpha_composite(out, s)
    main = Image.new('RGBA', (Wl, Hl), (0, 0, 0, 0))
    ImageDraw.Draw(main).multiline_text((ox, oy), text, font=fnt, fill=fill, align=align, spacing=spacing,
                                        stroke_width=stroke, stroke_fill=stroke_fill)
    if gradient:
        m = Image.new('L', (Wl, Hl), 0)
        ImageDraw.Draw(m).multiline_text((ox, oy), text, font=fnt, fill=255, align=align, spacing=spacing)
        grad = vgradient(Wl, Hl, gradient, y0=oy, y1=oy + th)
        main.paste(grad, (0, 0), m)
    out = Image.alpha_composite(out, main)
    return out

GOLD = [hexc('#fff3b0'), hexc('#ffd54a'), hexc('#e0a316'), hexc('#fff0a0')]
ROSEGOLD = [hexc('#ffe4e1'), hexc('#f4a6a0'), hexc('#c96f66'), hexc('#ffd9d4')]
SILVER = [hexc('#ffffff'), hexc('#d9dde3'), hexc('#8f97a3'), hexc('#f2f4f7')]

def reveal(layer, p, direction='lr', soft=60):
    """Wipe-reveal a layer: p 0..1, direction 'lr' (left->right), 'rl', 'tb', 'bt'. Returns new layer."""
    p = clamp01(p)
    if p >= 1: return layer
    w, h = layer.size
    if p <= 0: return Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if direction in ('lr', 'rl'):
        x = np.arange(w)[None, :]; edge = p * (w + soft) - soft
        a = np.clip((edge + soft - x) / soft, 0, 1)
        if direction == 'rl': a = a[:, ::-1]
        a = np.repeat(a, h, axis=0)
    else:
        y = np.arange(h)[:, None]; edge = p * (h + soft) - soft
        a = np.clip((edge + soft - y) / soft, 0, 1)
        if direction == 'bt': a = a[::-1, :]
        a = np.repeat(a, w, axis=1)
    out = layer.copy()
    out.putalpha(ImageChops.multiply(out.getchannel('A'), Image.fromarray((a * 255).astype(np.uint8), 'L')))
    return out

# ----------------------------------------------------------------------------- compositing
def paste_rgba(frame, layer, x, y):
    """alpha-composite layer at integer (x, y) with clipping."""
    fw, fh = frame.size; lw, lh = layer.size
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(fw, x + lw), min(fh, y + lh)
    if x1 <= x0 or y1 <= y0: return
    if (x0, y0, x1, y1) != (x, y, x + lw, y + lh):
        layer = layer.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    frame.alpha_composite(layer, (x0, y0))

def blit(frame, layer, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    """Composite an RGBA layer centred at (cx, cy) with optional scale / alpha / rotation (degrees)."""
    if alpha <= 0.002 or scale <= 0.002: return
    if layer.mode != 'RGBA': layer = layer.convert('RGBA')
    if abs(scale - 1) > 1e-3:
        nw, nh = max(1, int(round(layer.width * scale))), max(1, int(round(layer.height * scale)))
        layer = layer.resize((nw, nh), Image.LANCZOS if scale < 1 else Image.BICUBIC, reducing_gap=2.0)
    if rot: layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        layer = layer.copy(); layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    paste_rgba(frame, layer, int(round(cx - layer.width / 2)), int(round(cy - layer.height / 2)))

def blit_tl(frame, layer, x, y, alpha=1.0):
    blit(frame, layer, x + layer.width / 2, y + layer.height / 2, alpha=alpha)

def fill_rect(frame, box, color):
    ImageDraw.Draw(frame).rectangle(box, fill=color)

def tint(frame, color):
    """flat colour wash over whole frame (RGBA colour with alpha)."""
    frame.alpha_composite(Image.new('RGBA', frame.size, color))

def polaroid(i, w, caption='', angle=0.0, zoom=1.05, aspect=1.0, cap_font=None, cap_color=(60, 50, 50, 255),
             border=26, bottom=None, focus='girl', keep='auto', y_bias=0.0, paper=(252, 250, 246, 255), shadow_kw=None):
    """Polaroid-style card: photo (aspect w:h = aspect) on paper with a thick bottom strip for a hand-written caption."""
    pw = int(w - 2 * border); ph = int(pw / aspect)
    bottom = bottom if bottom is not None else int(w * 0.20)
    card = Image.new('RGBA', (int(w), ph + border + bottom), paper)
    im = fit(i, pw, ph, zoom=zoom, focus=focus, keep=keep, y_bias=y_bias)
    card.alpha_composite(rgba(im), (border, border))
    if caption:
        f = cap_font or font('Caveat[wght].ttf', int(w * 0.11), 'Bold')
        tl = text_layer(caption, f, fill=cap_color)
        blit(card, tl, w / 2, ph + border + bottom / 2)
    out = shadow(card, **(shadow_kw or dict(offset=(0, 16), blur=18, opacity=0.5)))
    if angle: out = out.rotate(angle, resample=Image.BICUBIC, expand=True)
    return out

# ----------------------------------------------------------------------------- particles
PASTEL = [hexc('#ff9ecd'), hexc('#ffd166'), hexc('#8ecae6'), hexc('#b8e994'), hexc('#c8a2ff'), hexc('#ff8a80'), hexc('#fff3b0')]
GOLDS = [hexc('#ffd54a'), hexc('#ffe9a8'), hexc('#e0a316'), hexc('#fff7d6')]
PINKS = [hexc('#ff6fae'), hexc('#ff9ecd'), hexc('#ffc1e3'), hexc('#ff4f93')]

def _rng(seed):
    return np.random.default_rng(seed)

def balloon_sprite(color, w=140):
    h = int(w * 1.28)
    s = Image.new('RGBA', (w * 2, int(h * 2 + w * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.ellipse((0, 0, w * 2 - 1, h * 2 - 1), fill=color)
    d.polygon([(w - w * 0.12, h * 2 - 6), (w + w * 0.12, h * 2 - 6), (w, h * 2 + w * 0.16)], fill=color)
    # highlight
    hl = Image.new('RGBA', s.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse((w * 0.5, h * 0.36, w * 0.95, h * 1.05), fill=(255, 255, 255, 120))
    hl = hl.filter(ImageFilter.GaussianBlur(w * 0.12))
    s = Image.alpha_composite(s, hl)
    # string
    d = ImageDraw.Draw(s)
    pts = [(w + math.sin(k / 6) * w * 0.12, h * 2 + w * 0.16 + k * (w * 1.4) / 30) for k in range(31)]
    d.line(pts, fill=(255, 255, 255, 170), width=3)
    return s.resize((s.width // 2, s.height // 2), Image.LANCZOS)

def sparkle_sprite(size, color=(255, 255, 255, 255)):
    s = Image.new('RGBA', (size * 2, size * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(s); c = size
    d.polygon(star_points(c, c, size * 0.98, n=4, inner=0.18), fill=color)
    glow = radial_sprite(size * 2, with_alpha(color, 140), power=2.5)
    out = Image.alpha_composite(glow, s)
    return out

def heart_sprite(size, color):
    s = Image.new('RGBA', (size * 2, size * 2), (0, 0, 0, 0))
    ImageDraw.Draw(s).polygon(heart_points(size * 2, size * 2), fill=color)
    return s.resize((size, size), Image.LANCZOS)

def star_sprite(size, color):
    s = Image.new('RGBA', (size * 2, size * 2), (0, 0, 0, 0))
    ImageDraw.Draw(s).polygon(star_points(size, size, size * 0.98, n=5, inner=0.5), fill=color)
    return s.resize((size, size), Image.LANCZOS)

class Particles:
    """Deterministic particle field. kinds: 'confetti', 'balloon', 'sparkle', 'bokeh', 'heart', 'petal', 'star', 'streamer'.
    draw(frame, t): t in seconds (global). Use t_offset so fields start 'already falling'."""
    def __init__(self, kind, n=60, seed=1, colors=None, size=(12, 28), speed=(80, 200), sway=40, alpha=1.0,
                 t_offset=6.0, spin=True, area=(W, H), drift=0.0, twinkle=1.2):
        self.kind, self.n, self.alpha, self.sway, self.t_off = kind, n, alpha, sway, t_offset
        self.spin, self.drift, self.twinkle = spin, drift, twinkle
        self.aw, self.ah = area
        r = _rng(seed)
        self.colors = colors or {'confetti': PASTEL, 'balloon': PASTEL, 'sparkle': [(255, 255, 255, 255)],
                                 'bokeh': GOLDS, 'heart': PINKS, 'petal': PINKS, 'star': GOLDS, 'streamer': PASTEL}[kind]
        self.x = r.uniform(0, self.aw, n); self.y = r.uniform(-self.ah * 0.2, self.ah * 1.2, n)
        self.sz = r.uniform(size[0], size[1], n); self.sp = r.uniform(speed[0], speed[1], n)
        self.ph = r.uniform(0, 2 * math.pi, n); self.fr = r.uniform(0.6, 1.6, n)
        self.rot = r.uniform(0, 360, n); self.rs = r.uniform(-180, 180, n)
        self.ci = r.integers(0, len(self.colors), n)
        self.shape = r.integers(0, 3, n)
        self.sprites = {}

    def _sprite(self, k, size, color):
        kk = (k, int(size), color)
        if kk not in self.sprites:
            if k == 'balloon': self.sprites[kk] = balloon_sprite(color, int(size))
            elif k == 'sparkle': self.sprites[kk] = sparkle_sprite(int(size), color)
            elif k == 'bokeh': self.sprites[kk] = radial_sprite(int(size), with_alpha(color, 150), power=1.4)
            elif k == 'heart': self.sprites[kk] = heart_sprite(int(size), color)
            elif k == 'star': self.sprites[kk] = star_sprite(int(size), color)
        return self.sprites[kk]

    def draw(self, frame, t):
        t = t + self.t_off
        k = self.kind
        if k in ('confetti', 'petal', 'streamer'):
            layer = Image.new('RGBA', frame.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
            for j in range(self.n):
                s = self.sz[j]
                y = (self.y[j] + self.sp[j] * t) % (self.ah + 4 * s) - 2 * s
                x = (self.x[j] + self.sway * math.sin(t * self.fr[j] + self.ph[j]) + self.drift * t) % (self.aw + 2 * s) - s
                col = with_alpha(self.colors[self.ci[j]], int(255 * self.alpha))
                a = math.radians(self.rot[j] + (self.rs[j] * t if self.spin else 0))
                if k == 'confetti':
                    w_, h_ = s, s * (0.45 + 0.35 * abs(math.sin(t * self.fr[j] * 2 + self.ph[j])))
                    if self.shape[j] == 2: w_, h_ = s * 0.7, s * 0.7
                    ca, sa = math.cos(a), math.sin(a)
                    pts = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx, dy in
                           ((-w_ / 2, -h_ / 2), (w_ / 2, -h_ / 2), (w_ / 2, h_ / 2), (-w_ / 2, h_ / 2))]
                    if self.shape[j] == 1: d.ellipse((x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2), fill=col)
                    else: d.polygon(pts, fill=col)
                elif k == 'petal':
                    w_, h_ = s, s * 0.55; ca, sa = math.cos(a), math.sin(a)
                    pts = []
                    for q in range(16):
                        th = 2 * math.pi * q / 16; dx, dy = w_ / 2 * math.cos(th), h_ / 2 * math.sin(th)
                        pts.append((x + dx * ca - dy * sa, y + dx * sa + dy * ca))
                    d.polygon(pts, fill=col)
                else:  # streamer: short wavy ribbon
                    pts = [(x + math.sin((y + q * 6) / 25 + self.ph[j]) * s * 0.4, y + q * 6) for q in range(10)]
                    d.line(pts, fill=col, width=max(2, int(s * 0.18)))
            frame.alpha_composite(layer)
        elif k in ('balloon', 'heart', 'star'):
            for j in range(self.n):
                s = self.sz[j]; spr = self._sprite(k, s, self.colors[self.ci[j]])
                if k == 'balloon' or k == 'heart':
                    y = self.ah + spr.height - ((self.y[j] + self.sp[j] * t) % (self.ah + 2 * spr.height))
                else:
                    y = (self.y[j] + self.sp[j] * t) % (self.ah + 2 * s) - s
                x = self.x[j] + self.sway * math.sin(t * self.fr[j] * 0.7 + self.ph[j])
                rot = (self.rs[j] * 0.15 * t if self.spin and k != 'balloon' else 4 * math.sin(t * self.fr[j] + self.ph[j]))
                blit(frame, spr, x, y, alpha=self.alpha, rot=rot if k != 'heart' else 0)
        elif k in ('sparkle', 'bokeh'):
            for j in range(self.n):
                s = self.sz[j]; spr = self._sprite(k, s, self.colors[self.ci[j]])
                tw = 0.5 + 0.5 * math.sin(t * self.fr[j] * self.twinkle * 2 + self.ph[j])
                a = (tw ** 2.2) * self.alpha if k == 'sparkle' else (0.35 + 0.65 * tw) * self.alpha
                x = (self.x[j] + self.drift * t + self.sway * 0.3 * math.sin(t * 0.3 * self.fr[j] + self.ph[j])) % self.aw
                y = (self.y[j] - self.sp[j] * 0.15 * t) % self.ah
                sc = 0.75 + 0.35 * tw
                blit(frame, spr, x, y, scale=sc if k == 'sparkle' else 1.0, alpha=a)

class LightLeak:
    """Slow-moving warm/colour light blobs (cheap cinematic flare)."""
    def __init__(self, colors=None, n=3, seed=3, size=900, alpha=0.5, speed=0.08):
        r = _rng(seed); self.n = n; self.alpha = alpha; self.speed = speed
        cols = colors or [hexc('#ffb36b'), hexc('#ff6fae'), hexc('#ffd54a')]
        self.spr = [radial_sprite(size, with_alpha(cols[k % len(cols)], 255), power=2.2) for k in range(n)]
        self.ph = r.uniform(0, 6.28, n); self.fr = r.uniform(0.6, 1.3, n)
    def draw(self, frame, t):
        for k in range(self.n):
            x = W / 2 + W * 0.65 * math.sin(t * self.speed * self.fr[k] * 2 + self.ph[k])
            y = H / 2 + H * 0.55 * math.cos(t * self.speed * self.fr[k] * 1.3 + self.ph[k] * 1.7)
            blit(frame, self.spr[k], x, y, alpha=self.alpha * (0.6 + 0.4 * math.sin(t * self.fr[k] + self.ph[k])))

# ----------------------------------------------------------------------------- transitions
def _rgb(a): return a.convert('RGB') if a.mode != 'RGB' else a
def tr_fade(a, b, p): return Image.blend(a, b, p)
def tr_cut(a, b, p): return b if p >= 0.5 else a
def tr_black(a, b, p):
    """dip to black."""
    if p < 0.5: return Image.blend(a, Image.new('RGBA', a.size, (0, 0, 0, 255)), p * 2)
    return Image.blend(Image.new('RGBA', a.size, (0, 0, 0, 255)), b, (p - 0.5) * 2)
def tr_white(a, b, p):
    if p < 0.5: return Image.blend(a, Image.new('RGBA', a.size, (255, 255, 255, 255)), p * 2)
    return Image.blend(Image.new('RGBA', a.size, (255, 255, 255, 255)), b, (p - 0.5) * 2)
def _push(a, b, p, dx, dy):
    e = ease_in_out_cubic(p)
    out = Image.new('RGBA', a.size, (0, 0, 0, 255))
    out.paste(a, (int(-dx * e), int(-dy * e)))
    out.paste(b, (int(dx * (1 - e)), int(dy * (1 - e))))
    return out
def tr_push_left(a, b, p): return _push(a, b, p, W, 0)
def tr_push_right(a, b, p): return _push(a, b, p, -W, 0)
def tr_push_up(a, b, p): return _push(a, b, p, 0, H)
def tr_push_down(a, b, p): return _push(a, b, p, 0, -H)
def tr_slide_over(a, b, p):
    e = ease_out_quint(p); out = a.copy(); out.paste(b, (int(W * (1 - e)), 0)); return out
def tr_slide_up_over(a, b, p):
    e = ease_out_quint(p); out = a.copy(); out.paste(b, (0, int(H * (1 - e)))); return out
def _scale_center(img, s):
    nw, nh = int(img.width * s), int(img.height * s)
    im = img.resize((nw, nh), Image.BILINEAR)
    out = Image.new('RGBA', img.size, (0, 0, 0, 255))
    out.paste(im, ((img.width - nw) // 2, (img.height - nh) // 2))
    return out
def tr_zoom(a, b, p):
    """a zooms in and fades out while b zooms from 0.92 to 1."""
    e = ease_in_out(p)
    az = _scale_center(a, 1 + 0.25 * e)
    bz = _scale_center(b, lerp(0.9, 1.0, ease_out_cubic(p))) if p < 1 else b
    return Image.blend(az, bz, e)
def tr_zoom_out(a, b, p):
    e = ease_in_out(p)
    az = _scale_center(a, lerp(1.0, 0.85, e))
    return Image.blend(az, b, e)
def tr_circle(a, b, p):
    e = ease_in_out(p)
    r = int(e * math.hypot(W, H) / 2 + 2)
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(30))
    return Image.composite(b, a, m)
def tr_heart(a, b, p):
    e = ease_in_out(p); s = int(e * H * 1.6 + 4)
    m = Image.new('L', (W, H), 0)
    hp = heart_points(s, s)
    ImageDraw.Draw(m).polygon([(x - s / 2 + W / 2, y - s / 2 + H / 2) for x, y in hp], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(20))
    return Image.composite(b, a, m)
def tr_wipe_diag(a, b, p):
    e = ease_in_out(p)
    m = Image.new('L', (W, H), 0)
    d = (W + H) * e * 1.15 - 0.15 * (W + H)
    ImageDraw.Draw(m).polygon([(0, 0), (d, 0), (0, d)] if d < 0 else [(0, 0), (d, 0), (0, d)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(40))
    return Image.composite(b, a, m)
def tr_blur(a, b, p):
    e = ease_in_out(p); r = 36 * math.sin(math.pi * e)
    x = Image.blend(a, b, e)
    return x.filter(ImageFilter.GaussianBlur(r)) if r > 1 else x
def tr_blinds(a, b, p, n=8):
    e = ease_in_out(p); m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m); bh = H / n
    for k in range(n): d.rectangle((0, k * bh, W, k * bh + bh * e + 1), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(6))
    return Image.composite(b, a, m)
def tr_flash(a, b, p):
    """quick white flash then b."""
    if p < 0.3: return Image.blend(a, Image.new('RGBA', a.size, (255, 255, 255, 255)), ease_in_cubic(p / 0.3))
    return Image.blend(Image.new('RGBA', a.size, (255, 255, 255, 255)), b, ease_out_cubic((p - 0.3) / 0.7))

TRANSITIONS = {'fade': tr_fade, 'cut': tr_cut, 'black': tr_black, 'white': tr_white, 'push_left': tr_push_left,
               'push_right': tr_push_right, 'push_up': tr_push_up, 'push_down': tr_push_down, 'slide_over': tr_slide_over,
               'slide_up_over': tr_slide_up_over, 'zoom': tr_zoom, 'zoom_out': tr_zoom_out, 'circle': tr_circle,
               'heart': tr_heart, 'wipe_diag': tr_wipe_diag, 'blur': tr_blur, 'blinds': tr_blinds, 'flash': tr_flash}

# ----------------------------------------------------------------------------- timeline
class Slide:
    def __init__(self, dur, render, trans='fade', tdur=0.6, name=''):
        self.dur, self.render, self.trans, self.tdur, self.name = float(dur), render, trans, float(tdur), name

class Timeline:
    """Sequence of slides with overlapping transitions (xfade semantics: duration = sum(dur) - sum(tdur[1:])).
    render(t) must return a W x H RGBA (or RGB) image for local time t in [0, dur].
    overlays: list of fn(frame, t_global) applied after slides (particles, vignette, watermark...)."""
    def __init__(self):
        self.slides = []; self.overlays = []
    def add(self, dur, render, trans='fade', tdur=0.6, name=''):
        self.slides.append(Slide(dur, render, trans, tdur, name)); return self
    def starts(self):
        st = []; t = 0.0
        for k, s in enumerate(self.slides):
            if k > 0: t -= s.tdur
            st.append(t); t += s.dur
        return st
    @property
    def duration(self):
        st = self.starts()
        return st[-1] + self.slides[-1].dur if self.slides else 0.0
    def frame(self, t, with_overlays=True):
        st = self.starts(); n = len(self.slides)
        idx = 0
        for k in range(n):
            if t >= st[k]: idx = k
        s = self.slides[idx]; tl = t - st[idx]
        if idx + 1 < n and t >= st[idx + 1] - 1e-9:
            idx = idx + 1; s = self.slides[idx]; tl = t - st[idx]
        fr = rgba(s.render(min(tl, s.dur)))
        if idx > 0 and tl < s.tdur and s.trans != 'cut':
            prev = self.slides[idx - 1]; tp = t - st[idx - 1]
            pa = rgba(prev.render(min(tp, prev.dur)))
            fr = TRANSITIONS[s.trans](pa, fr, clamp01(tl / s.tdur))
        if with_overlays:
            for fn in self.overlays: fn(fr, t)
        return fr

# ----------------------------------------------------------------------------- encoding / QA
def _render_segment(tl, f0, f1, path, fps, crf, preset):
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(fps), '-i', '-', '-an', '-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-pix_fmt', 'yuv420p',
           '-x264-params', 'keyint=60:min-keyint=30', '-threads', '2', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for f in range(f0, f1):
            fr = tl.frame(f / fps)
            p.stdin.write(fr.convert('RGB').tobytes())
    finally:
        p.stdin.close(); p.wait()
    if p.returncode != 0: raise RuntimeError(f'ffmpeg segment failed: {path}')

def encode(tl, out, audio=None, workers=3, fps=FPS, crf=18, preset='medium', audio_gain=1.0, verbose=True, audio_fade=2.0):
    """Render the timeline to an MP4 (H.264, yuv420p, faststart) with optional audio (wav/m4a path).
    audio_fade = length (s) of the final audio fade-out (default 2.0, as before)."""
    n = int(round(tl.duration * fps))
    tmp = tempfile.mkdtemp(prefix='bday_')
    bounds = [int(n * k / workers) for k in range(workers + 1)]
    segs = [os.path.join(tmp, f'seg{k:02d}.mp4') for k in range(workers)]
    if verbose: print(f'[encode] {out}: {n} frames, {tl.duration:.2f}s, {workers} workers')
    ctx = mp.get_context('fork')
    procs = [ctx.Process(target=_render_segment, args=(tl, bounds[k], bounds[k + 1], segs[k], fps, crf, preset)) for k in range(workers)]
    for p in procs: p.start()
    for p in procs: p.join()
    if any(p.exitcode != 0 for p in procs): raise RuntimeError('a render worker failed')
    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w') as f:
        for s in segs: f.write(f"file '{s}'\n")
    silent = os.path.join(tmp, 'video.mp4')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent], check=True)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if audio:
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', silent, '-i', audio, '-map', '0:v:0', '-map', '1:a:0',
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-af', f'volume={audio_gain},afade=t=out:st={max(0, tl.duration - audio_fade)}:d={audio_fade}',
                        '-shortest', '-movflags', '+faststart', out], check=True)
    else:
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', silent, '-c', 'copy', '-movflags', '+faststart', out], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    if verbose: print('[encode] done', out, os.path.getsize(out) // 1024, 'KB')
    return out

def snap(tl, t, out=None, scale=1.0):
    fr = tl.frame(t).convert('RGB')
    if scale != 1: fr = fr.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
    if out: fr.save(out, quality=90)
    return fr

def preview(tl, out, n=12, cols=4, scale=0.25, times=None):
    """Contact sheet of n evenly spaced frames (or explicit times) for QA."""
    times = times if times is not None else [tl.duration * (k + 0.5) / n for k in range(n)]
    tw, th = int(W * scale), int(H * scale); rows = math.ceil(len(times) / cols)
    sheet = Image.new('RGB', (cols * tw, rows * th), (30, 30, 30))
    f = ImageFont.truetype(os.path.join(FONT_DIR, 'Poppins-SemiBold.ttf'), 22)
    for k, t in enumerate(times):
        fr = snap(tl, t, scale=scale)
        d = ImageDraw.Draw(fr); d.rectangle((0, 0, 110, 30), fill=(0, 0, 0)); d.text((6, 3), f'{t:5.2f}s', font=f, fill=(255, 255, 0))
        sheet.paste(fr, ((k % cols) * tw, (k // cols) * th))
    sheet.save(out, quality=88)
    return out

def video_frames_sheet(mp4, out, n=12, cols=4, scale=0.25):
    """Contact sheet straight from an encoded mp4 (verifies the real output)."""
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4]).decode().strip())
    tmp = tempfile.mkdtemp(prefix='vf_'); tw, th = int(W * scale), int(H * scale); rows = math.ceil(n / cols)
    sheet = Image.new('RGB', (cols * tw, rows * th), (30, 30, 30))
    f = ImageFont.truetype(os.path.join(FONT_DIR, 'Poppins-SemiBold.ttf'), 22)
    for k in range(n):
        t = dur * (k + 0.5) / n; p = os.path.join(tmp, f'{k}.jpg')
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', f'{t:.3f}', '-i', mp4, '-frames:v', '1', '-q:v', '3', p], check=True)
        fr = Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS)
        d = ImageDraw.Draw(fr); d.rectangle((0, 0, 110, 30), fill=(0, 0, 0)); d.text((6, 3), f'{t:5.2f}s', font=f, fill=(255, 255, 0))
        sheet.paste(fr, ((k % cols) * tw, (k // cols) * th))
    sheet.save(out, quality=88); shutil.rmtree(tmp, ignore_errors=True)
    return out, dur
