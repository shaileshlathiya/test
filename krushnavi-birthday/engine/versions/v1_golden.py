#!/usr/bin/env python3
"""
v1_golden - "Golden Celebration" birthday status video for Krushnavi (round-2 fix).
1080x1920 @ 30 fps, ~29.6 s, H.264 + AAC (music-box Happy Birthday, hb_30s.wav).

ROUND-2 STRUCTURE: the whole film is ONE render function on global time. The navy/plum gradient and the
sparkle + bokeh fields run continuously; every "moment" (intro, 8 memory moments, finale) draws its content
on top. Cuts are SPATIAL, never dissolves: an outgoing photo is either pushed out, slid over (covered) or
opened like doors to reveal the incoming one - at no frame are two photos blended, and the content area is
never empty between two moments.  (`--check` renders every cut frame in probe mode and verifies this.)

CUTS (outgoing -> incoming)
  intro -> p07      intro content eases out, gold card rises in (tiny alpha hand-off, faces far apart)
  p07   -> p13      p13 full-bleed slides UP over the card (hard top edge while moving, soft fade restored after landing)
  p13   -> mom      push LEFT: p13 slides out left, the two mom tiles ride in from the right (train, never overlap)
  mom   -> p15      doors open VERTICALLY: top tile exits up, bottom tile exits down, revealing the tilted p15 card beneath
  p15   -> dad      the two dad tiles rise from below and cover the card (staggered), the card shrinks underneath
  dad   -> p01      doors open HORIZONTALLY onto p01's smile, which irises open beneath them (soft circle from her face)
  p01   -> fam      push UP: p01 slides out at the top, the fam tiles ride in from below
  fam   -> montage  FLASH CUT: additive gold bloom peaks exactly on the hard cut
  montage photos    cream in-card flash dips (one photo at a time, never two)
  montage -> finale FLASH CUT (same device), finale card settles 1.05 -> 1.0

STORYBOARD (global times, see --timing for the exact table)
  intro    0.00- 4.00   p11 gold circle (pre-rolled), "Happy Birthday" (Playfair Display Bold), "Krushnavi" writes on,
                        divider, "Many many happy returns of the day"; content eases out 3.65-4.0
  p07      3.90- 6.30   narrow 640x1240 gold card rises in (she fills it), KB 1.30->1.35, chip "Our little princess"
  p13      5.90- 8.55   full-bleed park smile, chip bottom-left "Little explorer"
  mom      8.15-11.10   p19 (top) + p04 (bottom) wide tiles, title "Mumma's love"
  p15     10.68-13.38   tilted card, chip "Pretty as a flower"
  dad     12.96-15.91   p14 tall + p10 narrow tiles, title "Daddy's girl"
  p01     15.61-18.16   full-bleed ball-pit smile, chip bottom-right "Our sunshine"
  fam     17.74-20.34   p03 + p09 tall tiles, title "Family festivals"
  montage 20.34-24.24   p05, p06, p16, p17 in a 3:4 gold card, chip "Moments we treasure"
  finale  24.24-29.64   p18 card, "Happy Birthday", "Krushnavi" writes on to the final cadence, "Lots of love, Mumma & Papa",
                        balloons in the side gutters, confetti (masked out of the text band), dim out over the last 0.6 s

Palette: midnight navy -> plum gradient, gold gradient type, cream captions.
Fonts: Playfair Display Bold (Happy Birthday), Great Vibes (name + collage titles), Poppins Medium (captions 44 px).
All photo crops go through fit()/kenburns() (face-safe); zoom <= 1.35; particles are drawn behind the photos.
"""
import sys, os, math, time, argparse
SCRATCH = os.environ.get('BDAY_DIR') or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # folder holding bday_engine.py, assets/, fonts/
sys.path.insert(0, SCRATCH)
from bday_engine import *

KEY = 'v1_golden'
OUT_DIR = os.path.join(SCRATCH, 'out')
os.makedirs(OUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------------- palette
NAVY = hexc('#0c1034'); NAVY_D = hexc('#08071e'); PLUM = hexc('#3c1548'); PLUM_D = hexc('#22103a')
GOLD1 = hexc('#ffd54a'); GOLD2 = hexc('#e0a316'); GOLD_L = hexc('#fff3b0'); CREAM = hexc('#fff4dc')
PINK_B = hexc('#e9a4cf')
GOLD_STROKE = (105, 60, 0, 255)
GOLD_SET = [GOLD1, GOLD_L, GOLD2, hexc('#fff7d6')]
SAFE_X0, SAFE_X1, SAFE_Y0, SAFE_Y1 = 70, 1010, 260, 1620
E_IO = ease_in_out_cubic          # the push / door motion curve

# ----------------------------------------------------------------------------- fonts
def fit_font(name, text, max_w, start, variation=None):
    """largest size <= start whose rendered width fits max_w."""
    s = start
    d = ImageDraw.Draw(Image.new('L', (4, 4)))
    while s > 24:
        f = font(name, s, variation)
        bb = d.textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] <= max_w: return f
        s -= 4
    return font(name, s, variation)

F_HB = fit_font('PlayfairDisplay[wght].ttf', 'Happy Birthday', 760, 92, 'Bold')
F_HB_SMALL = fit_font('PlayfairDisplay[wght].ttf', 'Happy Birthday', 640, 76, 'Bold')
F_NAME = font('GreatVibes-Regular.ttf', 200)
F_NAME_SMALL = font('GreatVibes-Regular.ttf', 165)
F_SCRIPT = font('GreatVibes-Regular.ttf', 124)
F_CAP = font('Poppins-Medium.ttf', 44)
F_SUB = font('Poppins-Medium.ttf', 44)

# ----------------------------------------------------------------------------- probe mode (QA only)
PROBE = None        # None = normal render; 'photo' = photos as white shapes, no sprites/text; 'face' = face boxes only

def faces_px(i, tw, th, zoom, pan, focus, keep, y_bias):
    """face boxes (girl first) in crop pixel coords for the same crop fit() would make."""
    img = photo(i); sw, sh = img.size
    fp = focus_point(i, focus); fp = (fp[0], fp[1] + y_bias)
    if keep == 'auto': kp = faces(i, 'all') if zoom <= 1.3 else faces(i, 'girl')
    elif keep == 'girl': kp = faces(i, 'girl')
    elif keep == 'all': kp = faces(i, 'all')
    else: kp = keep
    box = cover_box(img, tw, th, fp, zoom, pan, kp)
    sc = tw / (box[2] - box[0])
    return [((b[0] * sw - box[0]) * sc, (b[1] * sh - box[1]) * sc, (b[2] * sw - box[0]) * sc, (b[3] * sh - box[1]) * sc) for b in faces(i, 'all')]

def shot(i, tw, th, zoom=1.0, pan=(0, 0), focus='girl', keep='auto', y_bias=0.0):
    """face-safe crop (engine fit) - or a probe layer in QA mode."""
    if PROBE is None: return fit(i, tw, th, zoom=zoom, pan=pan, focus=focus, keep=keep, y_bias=y_bias)
    if PROBE == 'photo': return Image.new('RGBA', (int(tw), int(th)), (255, 255, 255, 255))
    lay = Image.new('RGBA', (int(tw), int(th)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for b in faces_px(i, tw, th, zoom, pan, focus, keep, y_bias): d.rectangle(b, fill=(255, 255, 255, 255))
    return lay

def kb(i, tw, th, u, z0=1.0, z1=1.12, p0=(0, 0), p1=(0, 0), **kw):
    """Ken Burns through shot(): u 0..1 -> zoom z0->z1, pan p0->p1 (ease_in_out_sine like the engine)."""
    e = ease_in_out_sine(clamp01(u))
    return shot(i, tw, th, lerp(z0, z1, e), (lerp(p0[0], p1[0], e), lerp(p0[1], p1[1], e)), **kw)

# ----------------------------------------------------------------------------- static layers (built once)
def build_bg():
    bg = vgradient(W, H, [hexc('#0e1238'), hexc('#2a1444'), hexc('#3c1548'), hexc('#1a0d33'), hexc('#0a0820')])
    paste_rgba(bg, radial_sprite(1500, (255, 196, 90, 60), power=2.0), 540 - 750, 230 - 750)   # warm top glow
    paste_rgba(bg, radial_sprite(1300, (150, 70, 160, 70), power=2.0), 820 - 650, 1500 - 650)  # plum bottom glow
    paste_rgba(bg, radial_sprite(1000, (255, 170, 80, 28), power=2.0), 120 - 500, 1200 - 500)
    return bg

BG = build_bg()

def glyph_box(layer, thr=120):
    a = np.array(layer.getchannel('A')); ys, xs = np.where(a > thr)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
def gcy(layer):
    """add to a target glyph-centre y to get the layer blit centre."""
    b = glyph_box(layer); return layer.height / 2 - (b[1] + b[3]) / 2

def gold_ring(r, width=12, glow=30):
    """Circular gold-gradient ring (inner radius r) with outer glow and a thin inner hairline. Centred sprite."""
    pad = glow * 2 + width + 24
    size = 2 * (r + pad)
    ss = 2
    big = Image.new('L', (size * ss, size * ss), 0)
    d = ImageDraw.Draw(big); c = size * ss / 2
    d.ellipse((c - (r + width) * ss, c - (r + width) * ss, c + (r + width) * ss, c + (r + width) * ss), fill=255)
    d.ellipse((c - r * ss, c - r * ss, c + r * ss, c + r * ss), fill=0)
    ring_m = big.resize((size, size), Image.LANCZOS)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    g = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    g.paste(Image.new('RGBA', (size, size), (255, 205, 90, 150)), (0, 0), ring_m)
    g = g.filter(ImageFilter.GaussianBlur(glow))
    out = Image.alpha_composite(out, g)
    grad = vgradient(size, size, [GOLD_L, GOLD1, GOLD2, GOLD_L, GOLD2], y0=pad, y1=size - pad)
    ring = Image.new('RGBA', (size, size), (0, 0, 0, 0)); ring.paste(grad, (0, 0), ring_m)
    out = Image.alpha_composite(out, ring)
    hl = Image.new('L', (size * ss, size * ss), 0); d = ImageDraw.Draw(hl)
    rr = r - 14
    d.ellipse((c - (rr + 2) * ss, c - (rr + 2) * ss, c + (rr + 2) * ss, c + (rr + 2) * ss), fill=255)
    d.ellipse((c - rr * ss, c - rr * ss, c + rr * ss, c + rr * ss), fill=0)
    hl = hl.resize((size, size), Image.LANCZOS)
    hl_rgba = Image.new('RGBA', (size, size), (0, 0, 0, 0)); hl_rgba.paste(Image.new('RGBA', (size, size), (255, 236, 170, 200)), (0, 0), hl)
    out = Image.alpha_composite(out, hl_rgba)
    return out, pad

class Tile:
    """Rounded gold-bordered photo tile with drop shadow. compose(img) -> RGBA layer (w+2pad, h+2pad)."""
    def __init__(self, w, h, radius=26, border=5, shadow_kw=None):
        self.w, self.h, self.r, self.b = w, h, radius, border
        ss = 2
        outer = Image.new('L', (w * ss, h * ss), 0)
        ImageDraw.Draw(outer).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radius=radius * ss, fill=255)
        inner = Image.new('L', (w * ss, h * ss), 0)
        ImageDraw.Draw(inner).rounded_rectangle((border * ss, border * ss, (w - border) * ss - 1, (h - border) * ss - 1),
                                                radius=max(1, (radius - border) * ss), fill=255)
        outer = outer.resize((w, h), Image.LANCZOS); inner = inner.resize((w, h), Image.LANCZOS)
        ring_m = ImageChops.subtract(outer, inner)
        grad = vgradient(w, h, [GOLD_L, GOLD1, GOLD2, GOLD_L, GOLD2, GOLD1])
        ring = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ring.paste(grad, (0, 0), ring_m)
        solid = Image.new('RGBA', (w, h), (0, 0, 0, 255)); solid.putalpha(outer)
        sh = shadow(solid, **(shadow_kw or dict(offset=(0, 16), blur=22, opacity=0.55)))
        pad = (sh.width - w) // 2
        inv = Image.new('L', sh.size, 255); inv.paste(ImageChops.invert(outer), (pad, pad))
        sh.putalpha(ImageChops.multiply(sh.getchannel('A'), inv))      # shadow only outside the tile
        sh.alpha_composite(ring, (pad, pad))
        self.sprite, self.pad = sh, pad
        self.pw, self.ph = w - 2 * border + 4, h - 2 * border + 4
        self.mask = rounded_mask(self.pw, self.ph, max(2, radius - border + 2))
    def photo(self, i, **kw):
        return shot(i, self.pw, self.ph, **kw)
    def kb(self, i, u, **kw):
        return kb(i, self.pw, self.ph, u, **kw)
    def compose(self, img):
        lay = Image.new('RGBA', self.sprite.size, (0, 0, 0, 0))
        lay.alpha_composite(apply_mask(img, self.mask), (self.pad + self.b - 2, self.pad + self.b - 2))
        if PROBE is None: lay.alpha_composite(self.sprite)
        return lay

CHIP_PAD = 40   # shadow pad of the chip layer (blur 14*2 + off 8 + 4)
def chip(text):
    """Caption chip: navy glass pill, gold outline, cream Poppins Medium 44 text, tiny gold sparkles at both ends."""
    tl = text_layer(text, F_CAP, fill=CREAM, pad=4)
    sp = sparkle_sprite(10, GOLD1)
    padx, gap, pady = 48, 18, 20
    w = tl.width + 2 * padx + 2 * (sp.width + gap); h = tl.height + 2 * pady
    p = panel(w, h, radius=h // 2, fill=(16, 10, 46, 200), outline=GOLD1, width=2)
    blit(p, tl, w / 2, h / 2)
    blit(p, sp, padx + sp.width / 2, h / 2); blit(p, sp, w - padx - sp.width / 2, h / 2)
    return shadow(p, offset=(0, 8), blur=14, opacity=0.45)

def divider(w=420, h=28):
    """Thin gold line fading at both ends with a small diamond in the middle."""
    x = np.arange(w); a = np.clip(1 - np.abs(x - w / 2) / (w / 2), 0, 1) ** 0.6
    arr = np.zeros((h, w, 4), np.uint8)
    arr[:, :, 0] = GOLD1[0]; arr[:, :, 1] = GOLD1[1]; arr[:, :, 2] = GOLD1[2]
    cy = h // 2
    for dy, s in ((-1, 0.55), (0, 1.0), (1, 0.55)): arr[cy + dy, :, 3] = (a * 255 * s).astype(np.uint8)
    im = Image.fromarray(arr, 'RGBA')
    d = ImageDraw.Draw(im); r = 9
    d.polygon([(w / 2, cy - r), (w / 2 + r, cy), (w / 2, cy + r), (w / 2 - r, cy)], fill=GOLD_L)
    d.polygon([(w / 2 - 34, cy - 4), (w / 2 - 30, cy), (w / 2 - 34, cy + 4), (w / 2 - 38, cy)], fill=GOLD1)
    d.polygon([(w / 2 + 34, cy - 4), (w / 2 + 38, cy), (w / 2 + 34, cy + 4), (w / 2 + 30, cy)], fill=GOLD1)
    return im

def gold_text(text, fnt, glow_r=24, glow_s=1.1, stroke=3):
    return text_layer(text, fnt, gradient=GOLD, stroke=stroke, stroke_fill=GOLD_STROKE, shadow_c=(0, 0, 0, 150),
                      shadow_off=(0, 10), shadow_blur=14, glow=(255, 205, 95, 255), glow_radius=glow_r, glow_strength=glow_s)

# text layers - the NAME is the loudest element on both cards (bigger, same glow as the title, deeper stroke);
# "Happy Birthday" is set in Playfair Display Bold with a lighter glow so the two faces do not fight.
T_HB = gold_text('Happy Birthday', F_HB, glow_r=22, glow_s=0.7, stroke=2)
T_NAME = gold_text('Krushnavi', F_NAME, glow_r=30, glow_s=1.15, stroke=3)
T_SUB = text_layer('Many many happy returns of the day', F_SUB, fill=CREAM, shadow_c=(0, 0, 0, 150), shadow_blur=10)
T_HB2 = gold_text('Happy Birthday', F_HB_SMALL, glow_r=20, glow_s=0.7, stroke=2)
T_NAME2 = gold_text('Krushnavi', F_NAME_SMALL, glow_r=28, glow_s=1.15, stroke=3)
T_LOVE = text_layer('Lots of love, Mumma & Papa', F_SUB, fill=CREAM, shadow_c=(0, 0, 0, 190), shadow_blur=12)
T_MOM = gold_text("Mumma's love", F_SCRIPT, glow_r=22, stroke=2)
T_DAD = gold_text("Daddy's girl", F_SCRIPT, glow_r=22, stroke=2)
T_FAM = gold_text('Family festivals', F_SCRIPT, glow_r=22, stroke=2)
DIV = divider()
CHIPS = {k: chip(k) for k in ['Our little princess', 'Little explorer', 'Pretty as a flower', 'Our sunshine', 'Moments we treasure']}
TITLE_GY = 1535          # glyph-centre y of the collage titles (tiles end at 1450, glyph rows end ~1606)
CHIP_CY = 1558           # chip centre (chip rows ~1510-1606)

# tiles
R_CIRCLE = 330
RING, RING_PAD = gold_ring(R_CIRCLE)
CIRC_MASK = circle_mask(2 * R_CIRCLE + 8)
T_PORT = Tile(640, 1240, radius=30, border=6)
T_TILT = Tile(820, 1180, radius=30, border=6)
T_MONT = Tile(900, 1200, radius=30, border=6)
T_FINAL = Tile(760, 800, radius=34, border=6, shadow_kw=dict(offset=(0, 18), blur=26, opacity=0.6))
T_WIDE = Tile(940, 580, radius=26, border=5)
T_TALL = Tile(520, 1180, radius=26, border=5)
T_NARROW = Tile(400, 1180, radius=26, border=5)
T_COL = Tile(460, 1180, radius=26, border=5)

def fb_mask(soft_top=True):
    """full-bleed photo alpha: soft fade into the gradient at the very top (80-280) and bottom (1540-1740)."""
    y = np.arange(H).astype(float)
    a = np.clip((1740 - y) / 200, 0, 1)
    if soft_top: a = a * np.clip((y - 80) / 200, 0, 1)
    a = a * a * (3 - 2 * a)
    return Image.fromarray(np.repeat((a * 255).astype(np.uint8)[:, None], W, axis=1), 'L')
FB_MASK = fb_mask(True)
FB_MASK_HARDTOP = fb_mask(False)

def circle_reveal(cx, cy, r, soft=28):
    """soft circle mask (W x H, 'L') centred at (cx, cy) with radius r."""
    s = 4
    m = Image.new('L', (W // s, H // s), 0)
    if r > 1: ImageDraw.Draw(m).ellipse((cx / s - r / s, cy / s - r / s, cx / s + r / s, cy / s + r / s), fill=255)
    return m.filter(ImageFilter.GaussianBlur(soft / s)).resize((W, H), Image.BILINEAR)

def text_band_mask():
    """confetti is masked OUT of the finale text band (y 1100-1560, 60 px soft edges) so no particle reads as a glyph."""
    y = np.arange(H).astype(float)
    a = 1 - np.clip((y - 1040) / 60, 0, 1) * np.clip((1620 - y) / 60, 0, 1)
    return Image.fromarray(np.repeat((a * 255).astype(np.uint8)[:, None], W, axis=1), 'L')
BAND_MASK = text_band_mask()

def flash_layer():
    """additive gold bloom: core (255,243,208) -> edge (255,211,120), radial falloff from (540, 900), radius 1400."""
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt((x - 540.0) ** 2 + (y - 900.0) ** 2) / 1400.0
    a = np.clip(1 - r, 0, 1) ** 1.3
    core = np.array([255, 243, 208], float); edge = np.array([255, 211, 120], float)
    col = core[None, None, :] * (1 - np.clip(r, 0, 1))[:, :, None] + edge[None, None, :] * np.clip(r, 0, 1)[:, :, None]
    return (col * a[:, :, None]).astype(np.float32)          # premultiplied light, H x W x 3
FLASH = flash_layer()

def screen_flash(fr, k):
    """fr = fr screen (FLASH * k) - light is ADDED, never a flat tint."""
    if k <= 0.01: return fr
    arr = np.asarray(fr.convert('RGB'), dtype=np.float32)
    out = 255.0 - (255.0 - arr) * (1.0 - FLASH * (k / 255.0))
    rgb = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGB')
    fr.paste(rgb)
    return fr

# particle fields (global time) - sparkles + bokeh run through the whole film, confetti only in the finale
SPARK = Particles('sparkle', n=26, seed=11, size=(10, 30), colors=[GOLD_L, GOLD1, (255, 255, 255, 255)], alpha=0.85, speed=(40, 90), t_offset=4)
BOKEH = Particles('bokeh', n=16, seed=4, size=(50, 150), colors=[GOLD1, hexc('#ffb866'), hexc('#c77dff')], alpha=0.30, speed=(20, 60))
CONF_FIN = Particles('confetti', n=64, seed=8, colors=GOLD_SET, size=(10, 24), speed=(45, 110), sway=30, alpha=0.95)

def balloon2(color, w=90):
    """Shaded balloon sprite: base colour, darker lower-right shading, top-left highlight, knot and a wavy string."""
    ss = 2; h = int(w * 1.25); W2, H2 = w * ss, h * ss; ox = 6
    size = (W2 + 2 * ox, H2 + int(w * 1.75) * ss)
    s = Image.new('RGBA', size, (0, 0, 0, 0))
    bm = Image.new('L', size, 0); ImageDraw.Draw(bm).ellipse((ox, 0, ox + W2 - 1, H2 - 1), fill=255)
    s.paste(Image.new('RGBA', size, color), (0, 0), bm)
    sh = Image.new('RGBA', size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((ox + W2 * 0.2, H2 * 0.3, ox + W2 * 1.15, H2 * 1.1), fill=(40, 10, 30, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(w * 0.3)); sh.putalpha(ImageChops.multiply(sh.getchannel('A'), bm))
    s = Image.alpha_composite(s, sh)
    hl = Image.new('RGBA', size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse((ox + W2 * 0.2, H2 * 0.1, ox + W2 * 0.5, H2 * 0.42), fill=(255, 255, 255, 175))
    hl = hl.filter(ImageFilter.GaussianBlur(w * 0.11)); hl.putalpha(ImageChops.multiply(hl.getchannel('A'), bm))
    s = Image.alpha_composite(s, hl)
    d = ImageDraw.Draw(s)
    dark = (max(0, color[0] - 70), max(0, color[1] - 70), max(0, color[2] - 60), 255)
    kx = ox + W2 / 2
    d.polygon([(kx - w * 0.16, H2 - 6), (kx + w * 0.16, H2 - 6), (kx, H2 + w * 0.26)], fill=dark)
    pts = [(kx + math.sin(k / 5) * w * 0.14, H2 + w * 0.26 + k * (w * 1.45) / 30) for k in range(31)]
    d.line(pts, fill=(255, 240, 200, 190), width=4)
    return s.resize((size[0] // ss, size[1] // ss), Image.LANCZOS)

class Balloons:
    """A few balloons that start below the frame edge and rise in the side gutters (never over the card or the text)."""
    def __init__(self, items):
        self.items = [(x, balloon2(c, w), sp, dl, ph) for x, c, w, sp, dl, ph in items]
    def draw(self, fr, t):
        for x, spr, sp, dl, ph in self.items:
            tt = max(0.0, t - dl)
            y = H + spr.height / 2 + 10 - sp * tt
            if y < -spr.height: continue
            blit(fr, spr, x + 8 * math.sin(tt * 1.2 + ph), y, rot=5 * math.sin(tt * 0.9 + ph))

BALLOONS = Balloons([(92, GOLD1, 90, 300, 0.0, 0.0), (52, PINK_B, 76, 250, 0.5, 1.5), (100, CREAM, 84, 270, 1.05, 3.0),
                     (988, CREAM, 88, 285, 0.2, 2.0), (1028, GOLD1, 76, 255, 0.8, 4.0), (980, PINK_B, 84, 275, 1.3, 0.7)])

def fields(g):
    """continuous background: gradient + bokeh + sparkles (global time g)."""
    fr = BG.copy()
    BOKEH.draw(fr, g); SPARK.draw(fr, g)
    return fr

# ----------------------------------------------------------------------------- moments
class Moment:
    """name, duration, draw(fr, t, g, ex, en): t local, ex = exit progress (last ovl_out s), en = entry progress (first ovl_in s).
    order 'in_over': this (incoming) moment is drawn over the outgoing one; 'out_over': the outgoing stays on top (doors)."""
    def __init__(self, name, dur, draw, ovl_in=0.0, order='in_over', fade_lead=0.18):
        self.name, self.dur, self.draw, self.ovl_in, self.order = name, dur, draw, ovl_in, order
        self.t0 = 0.0; self.ovl_out = 0.0; self.fade_lead = fade_lead
    @property
    def t_out(self): return self.dur - self.ovl_out            # local time at which the next moment starts
    def hold_fade(self, t, lead=None, end_gap=0.02):
        """1 -> 0 fade for chips / titles ending end_gap s before the exit choreography starts."""
        lead = self.fade_lead if lead is None else lead
        return 1 - seg(t, self.t_out - lead - end_gap, self.t_out - end_gap)

MOMENTS = []
FLASH_T = []

# ---- intro
INTRO_D = 4.0
def d_intro(fr, t, g, ex, en):
    xo = seg(t, INTRO_D - 0.4, INTRO_D - 0.08)               # content eases out (gone at 3.92) before the p07 card rises in
    xs = lerp(1.0, 0.9, ease_in_cubic(xo)); a = 1 - ease_in_out_sine(xo)
    # gold-ringed circle with p11, pre-rolled so frame 0 already shows her (~84 % scale), slow zoom 1.22 -> 1.32
    u = ease_out_back(seg(t + 0.25, 0.0, 0.95))
    z = lerp(1.22, 1.32, ease_in_out_sine(seg(t, 0.4, INTRO_D)))
    ph = shot(11, 2 * R_CIRCLE + 8, 2 * R_CIRCLE + 8, zoom=z, focus='girl', keep='girl')
    lay = Image.new('RGBA', RING.size, (0, 0, 0, 0))
    lay.alpha_composite(apply_mask(ph, CIRC_MASK), (RING_PAD - 4, RING_PAD - 4))
    if PROBE is None: lay.alpha_composite(RING)
    cy = 880 + 6 * math.sin(t * 1.3)
    blit(fr, lay, 540, cy, scale=max(0.01, u) * xs, alpha=min(seg(t + 0.3, 0.0, 0.3), a))
    if PROBE is not None: return
    v = ease_out_cubic(seg(t, 0.3, 1.1))                     # title drops in
    blit(fr, T_HB, 540, lerp(310, 372, v), alpha=min(seg(t, 0.3, 0.85), a))
    p = seg(t, 1.1, 2.15)                                    # name writes on
    if p > 0: blit(fr, reveal(T_NAME, ease_in_out_sine(p), 'lr', soft=90), 540, 1385, alpha=a)
    w = seg(t, 2.0, 2.5)
    if w > 0: blit(fr, DIV, 540, 1516, scale=lerp(0.5, 1.0, ease_out_cubic(w)), alpha=min(w, a))
    s = ease_out_cubic(seg(t, 2.3, 2.9))
    if s > 0: blit(fr, T_SUB, 540, lerp(1596, 1576, s), alpha=min(s, a))

# ---- portrait cards / full-bleeds / collages
def draw_chip(fr, m, t, name, t0, side='center', end_gap=0.02):
    if PROBE is not None: return
    ch = CHIPS[name]
    c = ease_out_cubic(seg(t, t0, t0 + 0.5)) * m.hold_fade(t, end_gap=end_gap)
    if c <= 0: return
    cx = {'center': 540, 'left': 56 + ch.width / 2, 'right': 1024 - ch.width / 2}[side]
    blit(fr, ch, cx, lerp(CHIP_CY + 24, CHIP_CY, c), alpha=c)

def card_p07(m):
    """p07 in a narrow gold card: rises in after the intro; exit = covered by p13 sliding up (drifts up 24 px, scale 1.02)."""
    kbkw = dict(z0=1.3, z1=1.35, focus='girl', keep='girl', y_bias=0.28, p0=(0.07, 0), p1=(0.07, 0))
    def draw(fr, t, g, ex, en):
        lay = T_PORT.compose(T_PORT.kb(7, seg(t, 0, m.dur), **kbkw))
        e = ease_out_cubic(seg(t, 0, 0.75))
        q = ease_in_out_sine(ex)
        blit(fr, lay, 540, lerp(970, 880, e) - 24 * q + 4 * math.sin(g * 1.1), scale=1 + 0.02 * q, alpha=seg(t, 0, 0.3))
        draw_chip(fr, m, t, 'Our little princess', 0.4)
    return draw

def card_p15(m):
    """tilted card revealed beneath the opening mom tiles (slides in from the left); exit = shrinks under the rising dad tiles."""
    kbkw = dict(z0=1.06, z1=1.2, focus='girl', keep='girl', y_bias=0.18, p1=(-0.02, 0))
    def draw(fr, t, g, ex, en):
        lay = T_TILT.compose(T_TILT.kb(15, seg(t, 0, m.dur), **kbkw))
        e = ease_out_cubic(seg(t, 0, 0.75))
        q = ease_in_out_sine(ex)
        blit(fr, lay, lerp(440, 540, e), 880 + 4 * math.sin(g * 1.1), scale=lerp(1.0, 0.86, q), rot=-2.5,
             alpha=min(seg(t, 0, 0.15), 1 - seg(ex, 0.76, 1.0)))
        draw_chip(fr, m, t, 'Pretty as a flower', m.ovl_in + 0.2)
    return draw

def fullbleed_p13(m):
    """slides UP over the p07 card (hard top edge while moving, soft top restored after landing); exit = push left."""
    kbkw = dict(z0=1.15, z1=1.28, focus='girl', keep='girl', y_bias=0.15)
    def draw(fr, t, g, ex, en):
        img = rgba(kb(13, W, H, seg(t, 0, m.dur), **kbkw))
        dy = int(round(H * (1 - E_IO(en))))
        dx = -int(round(W * E_IO(ex)))
        s = seg(t, m.ovl_in, m.ovl_in + 0.3)
        mk = FB_MASK if s >= 1 else (FB_MASK_HARDTOP if s <= 0 else Image.blend(FB_MASK_HARDTOP, FB_MASK, s))
        img.putalpha(mk)
        paste_rgba(fr, img, dx, dy)
        draw_chip(fr, m, t, 'Little explorer', m.ovl_in + 0.2, 'left')
    return draw

def fullbleed_p01(m):
    """irises open beneath the opening dad tiles (soft circle from her face); exit = push up."""
    kbkw = dict(z0=1.0, z1=1.12, focus='girl', keep='girl', y_bias=0.03)
    def draw(fr, t, g, ex, en):
        img = rgba(kb(1, W, H, seg(t, 0, m.dur), **kbkw))
        r = 1500 * E_IO(seg(t, 0, 0.5))
        mk = FB_MASK if r >= 1400 else ImageChops.multiply(FB_MASK, circle_reveal(540, 980, r))
        img.putalpha(mk)
        if r < 1: return
        paste_rgba(fr, img, 0, -int(round(H * E_IO(ex))))
        draw_chip(fr, m, t, 'Our sunshine', 0.55, 'right')
    return draw

def collage(m, layout, title, enter, exit_style, title_t0, lag=0.05):
    """layout: list of (tile, photo_id, cx, cy, kb_kw).  enter: 'push_left' | 'rise' | 'push_up'.
    exit_style: 'doors_v' (top tile up, bottom tile down) | 'doors_h' (left tile left, right tile right) | 'flash' (scale 1.04)."""
    ty = TITLE_GY + gcy(title)
    def draw(fr, t, g, ex, en):
        u = seg(t, 0, m.dur)
        for k, (tile, i, cx, cy, kw) in enumerate(layout):
            lay = tile.compose(tile.kb(i, u, **kw))
            p = E_IO(seg(t - k * lag, 0, m.ovl_in)) if m.ovl_in > 0 else 1.0
            dx = dy = 0.0; sc = 1.0
            if enter == 'push_left': dx = W * (1 - p)
            elif enter == 'rise': dy = 1700 * (1 - p)
            elif enter == 'push_up': dy = 1750 * (1 - p)
            q = E_IO(ex)
            if exit_style == 'doors_v': dy += (-1080 if k == 0 else 1080) * q
            elif exit_style == 'doors_h': dx += (-620 if k == 0 else 620) * q
            elif exit_style == 'flash': sc = 1 + 0.04 * ease_in_cubic(seg(t, m.dur - 0.12, m.dur))
            blit(fr, lay, cx + dx, cy + dy, scale=sc)
        if PROBE is not None: return
        p = seg(t, title_t0, title_t0 + 0.6); fade = m.hold_fade(t, end_gap=0.1 if exit_style == 'flash' else 0.02)
        if p > 0 and fade > 0: blit(fr, reveal(title, ease_in_out_sine(p), 'lr', soft=80), 540, ty, alpha=fade)
    return draw

# quick montage: 4 photos in a 3:4 gold card (p05, p06, p16, p17 - ends on her); swaps are cream in-card flash dips
MONT = [(5, dict(zoom=1.3, focus='all', keep='all'), 1.03), (6, dict(zoom=1.3, focus='all', keep='all'), 1.03),
        (16, dict(zoom=1.0, focus='all', keep='all'), 1.05), (17, dict(zoom=1.1, focus='girl', y_bias=0.1), 1.05)]
MONT_T = [0.0, 1.0, 1.9, 2.75]
MONT_D = 3.9
DIP_OUT, DIP_IN = 0.07, 0.10
CREAM_RGB = (255, 244, 222)
def montage(m):
    def draw(fr, t, g, ex, en):
        k = max(j for j in range(4) if MONT_T[j] <= t + 1e-6); tk = t - MONT_T[k]
        i, kw, drift = MONT[k]
        kw = dict(kw); kw['zoom'] = kw['zoom'] * lerp(1.0, drift, seg(tk, 0, 1.3))
        img = T_MONT.photo(i, **kw)
        if PROBE is None:
            b = 0.0
            if k > 0 and tk < DIP_IN: b = 1 - ease_out_cubic(seg(tk, 0, DIP_IN))                 # arrives out of the flash
            if k < 3: b = max(b, ease_in_cubic(seg(t, MONT_T[k + 1] - DIP_OUT, MONT_T[k + 1]))) # leaves into the flash
            if b > 0: img = Image.blend(img.convert('RGB'), Image.new('RGB', img.size, CREAM_RGB), b)
        lay = T_MONT.compose(img)
        sc = lerp(1.05 if k == 0 else 0.97, 1.0, ease_out_cubic(seg(tk, 0, 0.4)))
        sc *= 1 + 0.04 * ease_in_cubic(seg(t, m.dur - 0.12, m.dur))
        blit(fr, lay, 540, 890 + 4 * math.sin(g * 1.1), scale=sc)
        draw_chip(fr, m, t, 'Moments we treasure', 0.35, end_gap=0.12)
    return draw

# ---- finale
FIN_D = 5.4
FIN_CY = 690
def finale(m):
    hb_y = 1178 + gcy(T_HB2); name_y = 1358 + gcy(T_NAME2); love_y = 1522 + gcy(T_LOVE)
    def draw(fr, t, g, ex, en):
        if PROBE is None:
            conf = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            CONF_FIN.alpha = 0.95 * seg(t, 0.1, 0.9); CONF_FIN.draw(conf, g)
            conf.putalpha(ImageChops.multiply(conf.getchannel('A'), BAND_MASK))
            fr.alpha_composite(conf)
            BALLOONS.draw(fr, t)
        lay = T_FINAL.compose(T_FINAL.kb(18, seg(t, 0, m.dur), z0=1.26, z1=1.35, focus='girl', keep='girl', y_bias=0.14))
        blit(fr, lay, 540, FIN_CY + 4 * math.sin(g * 1.1), scale=lerp(1.05, 1.0, ease_out_cubic(seg(t, 0, 0.45))))
        if PROBE is not None: return
        v = ease_out_cubic(seg(t, 0.5, 1.2))
        if v > 0: blit(fr, T_HB2, 540, lerp(hb_y - 36, hb_y, v), alpha=v)
        p = seg(t, 2.1, 3.3)
        if p > 0: blit(fr, reveal(T_NAME2, ease_in_out_sine(p), 'lr', soft=90), 540, name_y)
        s = ease_out_cubic(seg(t, 3.0, 3.6))
        if s > 0: blit(fr, T_LOVE, 540, lerp(love_y + 16, love_y, s), alpha=s)
        f = seg(t, m.dur - 0.6, m.dur)
        if f > 0: tint(fr, (6, 5, 20, int(215 * ease_in_out_sine(f))))
    return draw

def build_moments():
    MOMENTS.clear()
    def add(name, dur, maker, ovl_in=0.0, order='in_over', **kw):
        m = Moment(name, dur, None, ovl_in, order); m.draw = maker(m, **kw) if kw else maker(m); MOMENTS.append(m); return m
    add('intro', INTRO_D, lambda m: d_intro)
    add('p07', 2.4, card_p07, ovl_in=0.1)
    add('p13', 2.65, fullbleed_p13, ovl_in=0.4)
    add('mom', 2.95, collage, ovl_in=0.4, layout=[(T_WIDE, 19, 540, 560, dict(focus='all', keep='all', z0=1.0, z1=1.08)),
                                                  (T_WIDE, 4, 540, 1160, dict(focus='all', keep='all', z0=1.18, z1=1.28))],
        title=T_MOM, enter='push_left', exit_style='doors_v', title_t0=0.5)
    add('p15', 2.7, card_p15, ovl_in=0.42, order='out_over')
    add('dad', 2.95, collage, ovl_in=0.42, layout=[(T_TALL, 14, 330, 860, dict(focus='all', keep='all', z0=1.0, z1=1.1)),
                                                   (T_NARROW, 10, 810, 860, dict(focus='all', keep='all', z0=1.1, z1=1.22))],
        title=T_DAD, enter='rise', exit_style='doors_h', title_t0=0.6, lag=0.06)
    add('p01', 2.55, fullbleed_p01, ovl_in=0.3, order='out_over')
    add('fam', 2.6, collage, ovl_in=0.42, layout=[(T_COL, 3, 300, 860, dict(focus='all', keep='all', z0=1.28, z1=1.35)),
                                                  (T_COL, 9, 780, 860, dict(focus='all', keep='all', z0=1.0, z1=1.08))],
        title=T_FAM, enter='push_up', exit_style='flash', title_t0=0.5, lag=0.04)
    add('montage', MONT_D, montage, ovl_in=0.0)
    add('finale', FIN_D, finale, ovl_in=0.0)
    t = 0.0
    for k, m in enumerate(MOMENTS):
        if k > 0: t -= m.ovl_in; MOMENTS[k - 1].ovl_out = m.ovl_in
        m.t0 = t; t += m.dur
    FLASH_T.clear(); FLASH_T.extend([by('montage').t0, by('finale').t0])
    return t
def by(name): return next(m for m in MOMENTS if m.name == name)
TOTAL = build_moments()

def active(g):
    return [m for m in MOMENTS if m.t0 - 1e-6 <= g < m.t0 + m.dur - 1e-6]

def draw_moment(fr, m, g):
    t = g - m.t0
    m.draw(fr, t, g, seg(t, m.dur - m.ovl_out, m.dur) if m.ovl_out > 0 else 0.0, seg(t, 0, m.ovl_in) if m.ovl_in > 0 else 1.0)

def render(g):
    fr = fields(g)
    ms = active(g)
    if len(ms) == 2 and ms[1].order == 'out_over': ms = [ms[1], ms[0]]
    for m in ms: draw_moment(fr, m, g)
    return fr

def flash_overlay(fr, t):
    """gold bloom: 0.08 s attack, ~2 peak frames (0.92) on the cut, 0.2 s decay - screen-composited (additive light)."""
    for ft in FLASH_T:
        d = t - ft
        if -0.08 <= d < 0.0: k = 0.92 * (1 - (1 - seg(d, -0.08, 0.0)) ** 2)
        elif 0.0 <= d < 0.24: k = 0.92 * (1 - ease_out_cubic(seg(d, 0.03, 0.24)))
        else: continue
        screen_flash(fr, k)

# ----------------------------------------------------------------------------- timeline
def build():
    tl = Timeline()
    tl.add(TOTAL, render, name='film')
    tl.overlays.append(lambda fr, t: fr.alpha_composite(vignette(0.32)))
    tl.overlays.append(flash_overlay)
    return tl

# ----------------------------------------------------------------------------- QA
def face_audit():
    """print face sizes (px on screen) and whether every face box stays inside each crop (with margin)."""
    def check(label, i, tw, th, zoom, focus='girl', keep='auto', y_bias=0.0, pan=(0, 0)):
        img = photo(i); sw, sh = img.size
        fp = focus_point(i, focus); fp = (fp[0], fp[1] + y_bias)
        kp = faces(i, 'all') if (keep == 'all' or (keep == 'auto' and zoom <= 1.3)) else (faces(i, 'girl') if keep in ('girl', 'auto') else None)
        box = cover_box(img, tw, th, fp, zoom, pan, kp)
        sc = tw / (box[2] - box[0])
        for j, b in enumerate(faces(i, 'all')):
            x0, y0, x1, y1 = b[0] * sw, b[1] * sh, b[2] * sw, b[3] * sh
            mg = min(x0 - box[0], box[2] - x1, y0 - box[1], box[3] - y1) * sc
            print(f'{label:22s} {key(i)} z={zoom:.2f} {"girl " if j == 0 else "other"} face {round((x1 - x0) * sc):4d}x{round((y1 - y0) * sc):4d} px  margin {mg:7.1f} px  {"OK" if mg >= 0 else "CLIPPED"}')
    check('intro circle', 11, 668, 668, 1.32, 'girl', 'girl')
    for z in (1.3, 1.35): check('p07 card', 7, T_PORT.pw, T_PORT.ph, z, 'girl', 'girl', 0.28, (0.07, 0))
    for z in (1.15, 1.28): check('p13 fullbleed', 13, W, H, z, 'girl', 'girl', 0.15)
    for z in (1.0, 1.08): check('mom p19 wide', 19, T_WIDE.pw, T_WIDE.ph, z, 'all', 'all')
    for z in (1.18, 1.28): check('mom p04 wide', 4, T_WIDE.pw, T_WIDE.ph, z, 'all', 'all')
    check('p15 tilt card', 15, T_TILT.pw, T_TILT.ph, 1.2, 'girl', 'girl', 0.18, (-0.02, 0))
    for z in (1.0, 1.1): check('dad p14 tall', 14, T_TALL.pw, T_TALL.ph, z, 'all', 'all')
    for z in (1.1, 1.22): check('dad p10 narrow', 10, T_NARROW.pw, T_NARROW.ph, z, 'all', 'all')
    for z in (1.0, 1.12): check('p01 fullbleed', 1, W, H, z, 'girl', 'girl', 0.03)
    for z in (1.28, 1.35): check('fam p03 col', 3, T_COL.pw, T_COL.ph, z, 'all', 'all')
    for z in (1.0, 1.08): check('fam p09 col', 9, T_COL.pw, T_COL.ph, z, 'all', 'all')
    for i, kw, drift in MONT:
        check('montage', i, T_MONT.pw, T_MONT.ph, kw['zoom'] * drift, kw['focus'], kw.get('keep', 'auto'), kw.get('y_bias', 0.0))
    for z in (1.26, 1.35): check('finale p18', 18, T_FINAL.pw, T_FINAL.ph, z, 'girl', 'girl', 0.14)
    # the reviewer's alternative fam layout (p09 as a 940x560 wide tile at zoom 1.35) - shown for the record
    check('ALT p09 wide 1.35', 9, 930, 554, 1.35, 'all', 'all')
    check('ALT p09 wide 1.00', 9, 930, 554, 1.0, 'all', 'all')

def probe_alpha(m, g, mode):
    """alpha map (H/4 x W/4, float 0..1) of moment m drawn alone in probe mode."""
    global PROBE
    PROBE = mode
    try:
        fr = Image.new('RGBA', (W, H), (0, 0, 0, 0)); draw_moment(fr, m, g)
    finally:
        PROBE = None
    return np.asarray(fr.getchannel('A'), dtype=np.float32) / 255.0

def erode(mask, n=2):
    """binary erosion by n px (3x3 cross, n times) - removes 1-px anti-aliased edges, keeps real soft overlaps."""
    m = mask.copy()
    for _ in range(n):
        e = m.copy()
        e[1:, :] &= m[:-1, :]; e[:-1, :] &= m[1:, :]; e[:, 1:] &= m[:, :-1]; e[:, :-1] &= m[:, 1:]
        m = e
    return m

def check_cuts(verbose=False, dump=False):
    """Double-exposure audit (full resolution): for every frame in which two moments are active, count pixels where
    both photos are visible and the top one is semi-transparent (blend pixels; 1-px anti-aliased tile edges are
    eroded away), and blend pixels inside any face box. Both must be 0 for a clean film."""
    worst = 0
    for k in range(1, len(MOMENTS)):
        A, B = MOMENTS[k - 1], MOMENTS[k]
        if B.ovl_in <= 0: continue
        f0 = int(math.floor(B.t0 * FPS)) - 1; f1 = int(math.ceil((B.t0 + B.ovl_in) * FPS)) + 2
        mx_bl = mx_fc = 0; bad = []
        for f in range(f0, f1 + 1):
            g = f / FPS
            if not (A.t0 <= g < A.t0 + A.dur and B.t0 <= g < B.t0 + B.dur): continue
            aA, aB = probe_alpha(A, g, 'photo'), probe_alpha(B, g, 'photo')
            fA, fB = probe_alpha(A, g, 'face'), probe_alpha(B, g, 'face')
            top, bot, ft, fb = (aB, aA, fB, fA) if B.order == 'in_over' else (aA, aB, fA, fB)
            blend = erode((top > 0.15) & (top < 0.85) & (bot > 0.15))
            face = blend & ((ft > 0.15) | (fb > 0.15))
            if dump and (blend.any()):
                dbg = Image.fromarray((np.stack([top, bot, blend.astype(np.float32)], -1) * 255).astype(np.uint8), 'RGB')
                dbg.resize((W // 2, H // 2)).save(os.path.join(OUT_DIR, f'{KEY}_probe_{f}.png'))
            nb, nf = int(blend.sum()), int(face.sum())
            mx_bl, mx_fc = max(mx_bl, nb), max(mx_fc, nf); worst = max(worst, nf)
            if nb or nf: bad.append((f, round(g, 3), nb, nf))
        print(f'cut {A.name:8s}->{B.name:8s} frames {f0}-{f1}: max blend px {mx_bl:6d}  max face-blend px {mx_fc:6d}  {"OK" if mx_fc == 0 and mx_bl == 0 else "CHECK"}')
        if verbose and bad: print('   ', bad)
    return worst

def timing_table():
    print('TOTAL %.2f s' % TOTAL)
    for m in MOMENTS:
        clean = m.dur - m.ovl_in - m.ovl_out
        print(f'  {m.name:8s} {m.t0:6.2f} - {m.t0 + m.dur:6.2f}  dur {m.dur:4.2f}  ovl_in {m.ovl_in:4.2f}  ovl_out {m.ovl_out:4.2f}  clean {clean:4.2f}  order {m.order}')
    print('  flashes at', [round(x, 2) for x in FLASH_T])

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true', help='only write preview sheets')
    ap.add_argument('--cuts', action='store_true', help='preview sheet of every cut (4 frames each)')
    ap.add_argument('--snap', type=float, nargs='*', help='snap half-size frames at these times')
    ap.add_argument('--timing', action='store_true')
    ap.add_argument('--audit', action='store_true', help='face size / clipping audit of every crop')
    ap.add_argument('--check', action='store_true', help='double-exposure audit of every cut (probe render)')
    args = ap.parse_args()
    tl = build()
    timing_table()
    if args.audit: face_audit()
    if args.check: check_cuts(verbose=True, dump=True)
    if args.timing:
        for t in (0.0, 1.0, 5.0, 6.1, 7.5, 8.3, 9.5, 10.9, 12.0, 13.1, 15.75, 16.5, 17.9, 20.35, 21.0, 24.3, 27.0, 29.5):
            t0 = time.time(); tl.frame(t); print('frame %.2f: %.3f s' % (t, time.time() - t0))
    if args.snap:
        for t in args.snap:
            snap(tl, t, os.path.join(OUT_DIR, f'{KEY}_snap_{t:05.2f}.jpg'), scale=0.5)
    if args.preview:
        preview(tl, os.path.join(OUT_DIR, f'{KEY}_prev_a.jpg'), n=16, cols=4, scale=0.3)
        keys = [0.0, 1.6, 3.2, 5.0, 7.2, 9.8, 12.2, 14.6, 17.0, 19.4, 21.3, 23.3, 24.6, 26.4, 28.0, 29.2]
        preview(tl, os.path.join(OUT_DIR, f'{KEY}_prev_b.jpg'), n=16, cols=4, scale=0.3, times=keys)
    if args.cuts:
        times = []
        for k in range(1, len(MOMENTS)):
            B = MOMENTS[k]; o = B.ovl_in if B.ovl_in > 0 else 0.3
            times += [round(B.t0 - 0.05, 3), round(B.t0 + o * 0.33, 3), round(B.t0 + o * 0.66, 3), round(B.t0 + o + 0.05, 3)]
        preview(tl, os.path.join(OUT_DIR, f'{KEY}_prev_cuts.jpg'), n=len(times), cols=4, scale=0.25, times=times)
    if args.preview or args.snap or args.timing or args.audit or args.check or args.cuts:
        sys.exit(0)
    out = os.path.join(OUT_DIR, f'{KEY}.mp4')
    t0 = time.time()
    encode(tl, out, audio=os.path.join(AUDIO_DIR, 'hb_30s.wav'), workers=3, preset='medium', crf=19)
    print('encode time %.1f s' % (time.time() - t0))
    video_frames_sheet(out, os.path.join(OUT_DIR, f'{KEY}_sheet.jpg'), n=16, cols=4, scale=0.3)
    video_frames_sheet(out, os.path.join(OUT_DIR, f'{KEY}_sheet_big.jpg'), n=8, cols=4, scale=0.5)
