#!/usr/bin/env python3
"""
v4_cakeday - "Cake Day Celebration" birthday status video for Krushnavi (9:16, 1080x1920, 30 fps, 29.5 s).
Built from the 11 NEW cake-cutting photos p20..p30 (the day itself).  Faces are never altered: every crop goes through
the engine's face-safe fit()/kenburns() (zoom <= 1.3), p26 (the cake, no faces) is rotated 180 deg so the piped name reads.

STORYBOARD (global times; timeline = sum(dur) - sum(tdur) = 29.5 s)  [round-1 fixes applied]
   0.00 -  4.00  INTRO      cream paper + big rounded card with p27 (hero: bunting + her + cake), slow KB 1.03->1.10,
                            "Happy Birthday" pops in at 1.2-1.8 s (lands on the first melody note, 1.4 s), "Krushnavi" writes on 1.9-2.9 s
                            below the card, confetti falls + 3 balloons bob BEHIND the card (never over her). Frame 0 shows her.
   3.60 -  6.30  CAKE       circle iris 0.4 -> p26 rotated 180 in a white-rimmed round "plate" over a caramel bokeh of the same
                            photo (brightness 0.85 + apricot veil); KB 1.0->1.08 toward the name + candles, pulsing glow + sparkles
                            on the two flames, pill "Make a wish" (58).
   5.90 -  8.60  p20        push_left  -> grandma (pink saree) feeding her, KB 1.0->1.12, pill "Cake time!" (bottom-left)
   8.20 - 10.95  p21        slide_over -> grandpa (white shirt) feeding her, KB 1.0->1.16 (push in), pill "Yummy!" (bottom-right)
  10.55 - 13.85  COLLAGE    push_up    -> cream paper, title "Blessings from our elders", two 880x556 tiles (p22 top KB 1.0->1.04,
                            p24 bottom KB 1.14->1.08), all elders' faces whole with >= 40 px tile room, her chin room 75-100 px
  13.45 - 16.20  p23        blur       -> grandma (teal blouse) feeding her, KB 1.0->1.1 + drift, pill "So much love" (left)
  15.80 - 18.90  p25        white dip  -> Mumma + Krushnavi + Papa at the table, KB 1.05->1.18 (focus all), pink pill "Mumma & Papa"
                            (60) on the table edge below the cake (cy 1555)
  18.50 - 21.20  p28        slide_up_over -> on Mumma's lap licking cream, KB 1.28->1.20 pushing in (faces in the upper third), pill "Sweetest bite"
  20.80 - 23.90  p29        push_right -> garden full-length, she sits in the left third (focus x 0.60), marigolds centre-right,
                            pill "Our sunshine" (star) bottom-right on the gravel, clear of her shoes
  23.40 - 29.50  FINALE     white dip  -> cream paper, square card with p30 (garden close-up, KB 1.14->1.24, face ~200-220 px),
                            "Happy Birthday" pops (24.1), "Krushnavi" writes on (24.8-25.8), pill "Lots of love, Mumma & Papa" (26.3),
                            4 balloons rise in the side gutters (x 90 / 990, inside the frame), confetti behind the card, 22 big sparkles
                            run around the card on the final chord (28.2 s), last 0.6 s dims gently (alpha 26) - never blank.

Transitions: circle(0.4), push_left, slide_over, push_up, blur, white(0.4), slide_up_over, push_right, white(0.5) - no black frame, no long crossfades.
Palette: cream paper #fff6ea (noise + peach/pink glows + faint sprinkles), bunting orange #f0963c, tee hot-pink #e83a8c,
         deep brown #4b2a30 captions, balloon pastels (rose, pink, yellow, orange, blue) for confetti/balloons.
Fonts:   display Fredoka Bold ("Happy Birthday", headings), name "Krushnavi" in Pacifico (allowed by the brief),
         supporting Quicksand Bold (caption pills).
Audio:   music.make_track(30.7 s, bpm 104) -> melody's final note + closing chord at 28.2 s; encode() trims to 29.5 s, 0.4 s fade (chord rings out), crf 23.
Flags:   --preview (sheets only), --check (geometry audit: faces/text/cards vs safe zone, text never over a face),
         --snap t.. (half-size frames), --timing (per-frame cost).
"""
import sys, os, math, time, argparse
SCRATCH = os.environ.get('BDAY_DIR') or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # folder holding bday_engine.py, assets/, fonts/
sys.path.insert(0, SCRATCH)
from bday_engine import *
import bday_engine as E

KEY = 'v4_cakeday'
OUT_DIR = os.path.join(SCRATCH, 'out')
os.makedirs(OUT_DIR, exist_ok=True)
SAFE = (70, 260, 1010, 1620)
AUDIO = os.path.join(AUDIO_DIR, 'hb_v4_307.wav')
PHOTOS_USED = ['p27', 'p26', 'p20', 'p21', 'p22', 'p24', 'p23', 'p25', 'p28', 'p29', 'p30']

# ----------------------------------------------------------------------------- palette
CREAM = hexc('#fff6ea')
ORANGE = hexc('#f0963c'); ORANGE_GRAD = [hexc('#ffc272'), hexc('#f0963c'), hexc('#d8721c')]
PINK = hexc('#e83a8c');   PINK_GRAD = [hexc('#ff80bb'), hexc('#ea3c8e'), hexc('#c21f6e')]
BROWN = hexc('#4b2a30')
WHITE = (255, 255, 255, 255)
BALLOON_COLS = [hexc('#f27d9d'), hexc('#f7b1ca'), hexc('#e4d75a'), hexc('#f5a24c'), hexc('#6fb5e9')]
CONFETTI_COLS = BALLOON_COLS + [hexc('#ffd27a'), hexc('#ff93c0')]

# ----------------------------------------------------------------------------- fonts
def F_DISP(s): return font('Fredoka[wdth,wght].ttf', s, 'Bold')
def F_CAP(s): return font('Quicksand[wght].ttf', s, 'Bold')
def F_NAME(s): return font('Pacifico-Regular.ttf', s)

def fit_size(mk, text, max_w, start):
    """largest size <= start whose plain rendering fits max_w."""
    d = ImageDraw.Draw(Image.new('L', (4, 4))); s = start
    while s > 20:
        bb = d.textbbox((0, 0), text, font=mk(s))
        if bb[2] - bb[0] <= max_w: return s
        s -= 2
    return s

_L = {}
def L(k, fn):
    if k not in _L: _L[k] = fn()
    return _L[k]

def display(text, size, grad=ORANGE_GRAD, stroke=7, max_w=840):
    size = fit_size(F_DISP, text, max_w, size)
    return text_layer(text, F_DISP(size), gradient=grad, stroke=stroke, stroke_fill=WHITE,
                      shadow_c=(90, 45, 25, 120), shadow_off=(0, 8), shadow_blur=12)

def name_layer(size):
    return text_layer('Krushnavi', F_NAME(size), gradient=PINK_GRAD, stroke=8, stroke_fill=WHITE,
                      shadow_c=(90, 30, 50, 130), shadow_off=(0, 8), shadow_blur=12)

PILL_PAD = 40     # shadow() pad for the pill shadow below (blur 14 -> 2*14 + 8 + 4)
def pill(text, size=56, fill=(255, 251, 244, 242), color=BROWN, icon='heart', icon_col=ORANGE, padx=48, pady=16):
    tl = text_layer(text, F_CAP(size), fill=color, pad=4)
    ic = heart_sprite(30, icon_col) if icon == 'heart' else (star_sprite(30, icon_col) if icon == 'star' else None)
    iw = (ic.width + 14) if ic is not None else 0
    w = tl.width + 2 * padx + iw; h = tl.height + 2 * pady
    p = panel(w, h, radius=h // 2, fill=fill)
    if ic is not None: blit(p, ic, padx + ic.width / 2, h / 2 + 1)
    blit(p, tl, padx + iw + tl.width / 2, h / 2)
    return shadow(p, offset=(0, 8), blur=14, opacity=0.26, color=(80, 40, 20))

# ----------------------------------------------------------------------------- static backgrounds (built once)
def make_cream(seed=4):
    r = np.random.default_rng(seed)
    arr = np.empty((H, W, 4), np.uint8); arr[:, :, :3] = CREAM[:3]; arr[:, :, 3] = 255
    arr[:, :, :3] = np.clip(arr[:, :, :3].astype(int) + r.integers(-3, 4, (H, W, 1)), 0, 255).astype(np.uint8)
    bg = Image.fromarray(arr, 'RGBA')
    blit(bg, radial_sprite(1700, with_alpha(hexc('#ffd6ad'), 255), power=1.7), 160, 240, alpha=0.62)    # peach glow (top-left)
    blit(bg, radial_sprite(1500, with_alpha(hexc('#ffc8da'), 255), power=1.7), 980, 1720, alpha=0.55)   # pink glow (bottom-right)
    blit(bg, radial_sprite(1300, with_alpha(hexc('#fff3cf'), 255), power=1.4), 540, 940, alpha=0.5)     # centre lift
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)                               # faint sprinkles
    for k in range(150):
        x, y = r.uniform(0, W), r.uniform(0, H); s = r.uniform(5, 12)
        c = CONFETTI_COLS[r.integers(0, len(CONFETTI_COLS))]; a = math.radians(r.uniform(0, 180))
        if r.random() < 0.45: d.ellipse((x - s / 2, y - s / 2, x + s / 2, y + s / 2), fill=c)
        else:
            dx, dy = math.cos(a) * s, math.sin(a) * s
            d.line((x - dx, y - dy, x + dx, y + dy), fill=c, width=max(3, int(s * 0.45)))
    lay.putalpha(lay.getchannel('A').point(lambda v: int(v * 0.30)))
    bg.alpha_composite(lay)
    return bg

BG = make_cream()
WARM = Image.new('RGBA', (W, H), (255, 190, 120, 14))       # ~5 % warm wash on the full-frame photos
VIG = vignette(0.22, power=2.4)

# ----------------------------------------------------------------------------- cards
class Card:
    """White rounded photo card with a soft warm shadow. compose(img) -> RGBA layer; .off = photo origin inside the layer."""
    def __init__(self, w, h, border=16, radius=44, round_=False, shadow_kw=None):
        self.pw, self.ph, self.b = w, h, border
        fw, fh = w + 2 * border, h + 2 * border
        m = circle_mask(fw, fh) if round_ else rounded_mask(fw, fh, radius)
        base = apply_mask(Image.new('RGBA', (fw, fh), WHITE), m)
        self.frame = shadow(base, **(shadow_kw or dict(offset=(0, 22), blur=30, opacity=0.30, color=(96, 48, 28))))
        self.pad = (self.frame.width - fw) // 2
        self.mask = circle_mask(w, h) if round_ else rounded_mask(w, h, max(2, radius - border))
        self.off = (self.pad + border, self.pad + border)
    def compose(self, img):
        lay = self.frame.copy()
        lay.alpha_composite(apply_mask(img, self.mask), self.off)
        return lay

# ----------------------------------------------------------------------------- face-safe shots (+ probe for --check)
_PROBE = None          # None or a list collecting (kind, bbox, tag) while a slide renders

def crop_box(i, tw, th, zoom, pan, focus, keep, y_bias, img=None):
    img = img if img is not None else photo(i)
    fp = focus_point(i, focus); fp = (fp[0], fp[1] + y_bias)
    if keep == 'auto': kp = faces(i, 'all') if zoom <= 1.3 else faces(i, 'girl')
    elif keep == 'girl': kp = faces(i, 'girl')
    elif keep == 'all': kp = faces(i, 'all')
    else: kp = keep
    return cover_box(img, tw, th, fp, zoom, pan, kp)

class Shot:
    """One photo move: zoom z0->z1 and pan p0->p1 over u in 0..1 (ease_in_out_sine), rendered through the engine's fit()."""
    def __init__(self, i, z0=1.0, z1=1.1, p0=(0, 0), p1=(0, 0), focus='all', keep='all', y_bias=0.0, img=None):
        self.i, self.z0, self.z1, self.p0, self.p1 = i, z0, z1, p0, p1
        self.focus, self.keep, self.y_bias, self.img = focus, keep, y_bias, img
        self.has_faces = meta(i).get('people') != 'cake'
    def params(self, u):
        e = ease_in_out_sine(clamp01(u))
        return lerp(self.z0, self.z1, e), (lerp(self.p0[0], self.p1[0], e), lerp(self.p0[1], self.p1[1], e))
    def render(self, tw, th, u):
        z, p = self.params(u)
        return rgba(fit(self.i, tw, th, zoom=z, pan=p, focus=self.focus, keep=self.keep, y_bias=self.y_bias, img=self.img))
    def box(self, tw, th, u):
        z, p = self.params(u)
        return crop_box(self.i, tw, th, z, p, self.focus, self.keep, self.y_bias, self.img)
    def point_px(self, tw, th, u, pt):
        img = self.img if self.img is not None else photo(self.i); sw, sh = img.size
        b = self.box(tw, th, u); sc = tw / (b[2] - b[0])
        return ((pt[0] * sw - b[0]) * sc, (pt[1] * sh - b[1]) * sc)
    def faces_px(self, tw, th, u):
        if not self.has_faces: return []
        img = self.img if self.img is not None else photo(self.i); sw, sh = img.size
        b = self.box(tw, th, u); sc = tw / (b[2] - b[0])
        return [((f[0] * sw - b[0]) * sc, (f[1] * sh - b[1]) * sc, (f[2] * sw - b[0]) * sc, (f[3] * sh - b[1]) * sc)
                for f in faces(self.i, 'all')]

def ink_bbox(layer, thr=110):
    bb = layer.getchannel('A').point(lambda v: 255 if v >= thr else 0).getbbox()
    return bb if bb else (0, 0, 0, 0)

def put(fr, layer, cx, cy, scale=1.0, alpha=1.0, tag=None):
    """blit + (in probe mode) record the ink bbox of the layer as placed."""
    blit(fr, layer, cx, cy, scale=scale, alpha=alpha)
    if _PROBE is not None and tag and alpha > 0.05 and scale > 0.05:
        b = ink_bbox(layer); lw, lh = layer.size
        x0, y0 = cx - lw * scale / 2, cy - lh * scale / 2
        _PROBE.append(('text', (x0 + b[0] * scale, y0 + b[1] * scale, x0 + b[2] * scale, y0 + b[3] * scale), tag))

def put_card(fr, card, img, cx, cy, s=1.0, alpha=1.0, shot=None, u=0.0, tag='card'):
    lay = card.compose(img)
    blit(fr, lay, cx, cy, scale=s, alpha=alpha)
    if _PROBE is not None:
        lw, lh = lay.size; x0, y0 = cx - lw * s / 2, cy - lh * s / 2
        fw, fh = card.pw + 2 * card.b, card.ph + 2 * card.b
        _PROBE.append(('card', (x0 + card.pad * s, y0 + card.pad * s, x0 + (card.pad + fw) * s, y0 + (card.pad + fh) * s), tag))
        if shot is not None:
            ox, oy = x0 + card.off[0] * s, y0 + card.off[1] * s
            for k, b in enumerate(shot.faces_px(card.pw, card.ph, u)):
                _PROBE.append(('girl' if k == 0 else 'other', (ox + b[0] * s, oy + b[1] * s, ox + b[2] * s, oy + b[3] * s), tag))

def record_full(shot, u, tag):
    if _PROBE is not None:
        for k, b in enumerate(shot.faces_px(W, H, u)):
            _PROBE.append(('girl' if k == 0 else 'other', b, tag))

def anchor_x(lay, where, pad=PILL_PAD):
    """centre x for a shadowed layer so its visible body sits at the left/right safe margin (or centred)."""
    if where == 'left': return 96 - pad + lay.width / 2
    if where == 'right': return 984 + pad - lay.width / 2
    return 540

# ----------------------------------------------------------------------------- sprites / particles
BAL = [balloon_sprite(c, 118) for c in BALLOON_COLS]
CONF_INTRO = Particles('confetti', n=34, seed=11, colors=CONFETTI_COLS, size=(9, 20), speed=(55, 110), sway=28, alpha=0.95, t_offset=9)
CONF_COL = Particles('confetti', n=22, seed=13, colors=CONFETTI_COLS, size=(8, 18), speed=(45, 90), sway=24, alpha=0.9, t_offset=4)
CONF_FIN = Particles('confetti', n=56, seed=12, colors=CONFETTI_COLS, size=(9, 22), speed=(70, 140), sway=30, alpha=0.95, t_offset=5)
GLOW = radial_sprite(300, (255, 200, 110, 255), power=1.6)
SPK = sparkle_sprite(16, (255, 244, 210, 255))
SPK_BIG = sparkle_sprite(40, (255, 214, 120, 255))

# ----------------------------------------------------------------------------- INTRO
INTRO_CARD = Card(800, 930, border=16, radius=44)
INTRO_SHOT = Shot(27, 1.03, 1.10, focus=(0.485, 0.44), keep='girl')
INTRO_BALLOONS = ((90, 1340, 0.0, 0), (990, 640, 2.1, 3), (992, 1380, 4.0, 4))     # (x, y, phase, colour)

def intro(dur):
    def render(t):
        fr = BG.copy()
        CONF_INTRO.draw(fr, t)
        for bx, by, ph, ci in INTRO_BALLOONS:                       # behind the card -> never over her
            y = by - 16 * t + 9 * math.sin(t * 1.3 + ph); x = bx + 6 * math.sin(t * 0.9 + ph)
            blit(fr, BAL[ci], x, y, rot=4 * math.sin(t * 1.1 + ph))
        s = 1 + 0.035 * (1 - ease_out_cubic(seg(t, 0, 0.9)))
        im = INTRO_SHOT.render(INTRO_CARD.pw, INTRO_CARD.ph, t / dur)
        put_card(fr, INTRO_CARD, im, 540, 926, s, shot=INTRO_SHOT, u=t / dur)
        hb = L('hb', lambda: display('Happy Birthday', 100))
        u1 = seg(t, 1.2, 1.8)                                           # lands on the first melody note (1.4 s)
        put(fr, hb, 540, 352, scale=0.55 + 0.45 * ease_out_back(u1), alpha=seg(t, 1.2, 1.45), tag='hb')
        nm = L('name', lambda: name_layer(140))
        u2 = seg(t, 1.9, 2.9)
        if u2 > 0: put(fr, reveal(nm, ease_in_out_sine(u2), 'lr', soft=90), 540, 1500, tag='name')
        return fr
    return render

# ----------------------------------------------------------------------------- CAKE
P26R = photo(26).rotate(180)
CAKE_DISC = Card(880, 880, border=14, round_=True, shadow_kw=dict(offset=(0, 24), blur=32, opacity=0.5, color=(25, 8, 4)))
CAKE_SHOT = Shot(26, 1.0, 1.08, focus=(0.525, 0.46), keep=None, img=P26R)
FLAMES = [(0.15, 0.565), (0.855, 0.51)]            # flame tips in the ROTATED image (normalized)

def cake_bg():
    small = fit(26, W // 4, H // 4, zoom=1.0, focus=(0.5, 0.45), keep=None, img=P26R).filter(ImageFilter.GaussianBlur(9))
    small = ImageEnhance.Brightness(small).enhance(0.85)
    bg = small.resize((W, H), Image.BILINEAR).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (255, 212, 168, 120)))     # warm apricot veil -> caramel bokeh
    blit(bg, radial_sprite(1500, (255, 165, 70, 255), power=1.8), 540, 870, alpha=0.55)
    return bg

def cake(dur):
    def render(t):
        fr = L('cakebg', cake_bg).copy()
        u = t / dur
        im = CAKE_SHOT.render(CAKE_DISC.pw, CAKE_DISC.ph, u)
        for k, fp in enumerate(FLAMES):
            x, y = CAKE_SHOT.point_px(CAKE_DISC.pw, CAKE_DISC.ph, u, fp)
            blit(im, GLOW, x, y - 6, scale=0.85 + 0.12 * math.sin(t * 7.3 + k), alpha=0.5 + 0.18 * math.sin(t * 9.1 + 2 * k))
            for q in range(6):
                ph = q * 1.25 + k * 0.7; r = 46 + 24 * q; ang = t * 1.3 + ph
                sx, sy = x + r * math.cos(ang), y - 12 + r * 0.55 * math.sin(ang * 1.4)
                tw_ = 0.5 + 0.5 * math.sin(t * 6.5 + q * 2.1 + k)
                blit(im, SPK, sx, sy, scale=0.45 + 0.55 * tw_, alpha=tw_ ** 2)
        s = 1 + 0.03 * (1 - ease_out_cubic(seg(t, 0, 0.9)))
        put_card(fr, CAKE_DISC, im, 540, 866, s, shot=CAKE_SHOT, u=u)
        cap = L('wish', lambda: pill('Make a wish', 58, icon='star'))
        u1 = seg(t, 0.55, 1.05)
        put(fr, cap, 540, 1452, scale=0.6 + 0.4 * ease_out_back(u1), alpha=seg(t, 0.55, 0.78), tag='cap')
        return fr
    return render

# ----------------------------------------------------------------------------- FULL-FRAME MOMENTS
def full(shot, dur, caption=None, where='left', cy=1500, cap_t=0.5, kind='pill', size=56, icon='heart', pink=False):
    def mk():
        if kind == 'display': return display(caption, size)
        if pink: return pill(caption, size, fill=PINK, color=WHITE, icon=icon, icon_col=WHITE)
        return pill(caption, size, icon=icon)
    def render(t):
        u = t / dur
        fr = shot.render(W, H, u)
        record_full(shot, u, key(shot.i))
        fr.alpha_composite(WARM); fr.alpha_composite(VIG)
        if caption:
            lay = L(('cap', caption, kind, size, pink), mk)
            uu = seg(t, cap_t, cap_t + 0.5)
            put(fr, lay, anchor_x(lay, where, PILL_PAD if kind == 'pill' else 0), cy,
                scale=0.6 + 0.4 * ease_out_back(uu), alpha=seg(t, cap_t, cap_t + 0.25), tag='cap')
        return fr
    return render

# ----------------------------------------------------------------------------- COLLAGE (p22 + p24)
TILE = Card(880, 556, border=14, radius=36, shadow_kw=dict(offset=(0, 18), blur=26, opacity=0.28, color=(96, 48, 28)))
COL = ((Shot(22, 1.0, 1.04, focus='all', keep='all'), 526, 724), (Shot(24, 1.14, 1.08, focus='all', keep='all'), 554, 1322))

def collage(dur):
    def render(t):
        fr = BG.copy()
        CONF_COL.draw(fr, t)
        u = t / dur
        s = 1 + 0.03 * (1 - ease_out_cubic(seg(t, 0, 0.8)))
        for shot, cx, cy in COL:
            put_card(fr, TILE, shot.render(TILE.pw, TILE.ph, u), cx, cy, s, shot=shot, u=u, tag=key(shot.i))
        title = L('bless', lambda: display('Blessings from our elders', 64, stroke=6, max_w=820))
        u1 = seg(t, 0.3, 0.9)
        put(fr, title, 540, 350, scale=0.6 + 0.4 * ease_out_back(u1), alpha=seg(t, 0.3, 0.55), tag='title')
        return fr
    return render

# ----------------------------------------------------------------------------- FINALE
FIN_CARD = Card(760, 760, border=16, radius=48)
FIN_SHOT = Shot(30, 1.14, 1.24, focus=(0.5, 0.33), keep='girl', y_bias=0.12)
SHIMMER_T = 28.2 - 23.4   # final chord (28.2 s in the track) in finale-local time (finale starts at 23.4 s)
FIN_BALLOONS = ((90, 1900, 95, 0.0, 0), (990, 2060, 112, 2.0, 1), (92, 2520, 150, 4.0, 2), (988, 2720, 160, 1.0, 4))

def finale(dur):
    def render(t):
        fr = BG.copy()
        CONF_FIN.draw(fr, t)
        for bx, y0, sp, ph, ci in FIN_BALLOONS:                        # rising in the side gutters, behind the card
            blit(fr, BAL[ci], bx + 9 * math.sin(t * 0.8 + ph), y0 - sp * t, rot=5 * math.sin(t + ph))
        s = 1 + 0.06 * (1 - ease_out_cubic(seg(t, 0, 1.0)))
        put_card(fr, FIN_CARD, FIN_SHOT.render(FIN_CARD.pw, FIN_CARD.ph, t / dur), 540, 880, s, shot=FIN_SHOT, u=t / dur)
        us = seg(t, SHIMMER_T, SHIMMER_T + 0.4)                          # shimmer around the card on the final chord
        if us > 0:
            for q in range(22):                                         # sparkles run along a rounded square just outside the card
                a = math.radians(q * 360 / 22 + 8 + 10 * t); rr = (430 + 8 * math.sin(t * 3 + q)) / max(abs(math.cos(a)), abs(math.sin(a)))
                tw_ = 0.5 + 0.5 * math.sin(t * 5 + q * 1.7)
                blit(fr, SPK_BIG, 540 + rr * math.cos(a), 880 + rr * math.sin(a), scale=0.7 + 0.8 * tw_, alpha=us * tw_ ** 2)
        hb = L('hb_fin', lambda: display('Happy Birthday', 86))
        u1 = seg(t, 0.7, 1.3)
        put(fr, hb, 540, 352, scale=0.55 + 0.45 * ease_out_back(u1), alpha=seg(t, 0.7, 0.95), tag='hb')
        nm = L('name_fin', lambda: name_layer(118))
        u2 = seg(t, 1.4, 2.4)
        if u2 > 0: put(fr, reveal(nm, ease_in_out_sine(u2), 'lr', soft=90), 540, 1372, tag='name')
        love = L('love', lambda: pill('Lots of love, Mumma & Papa', 52, icon='heart', icon_col=PINK))
        u3 = seg(t, 2.9, 3.5)
        put(fr, love, 540, 1522, scale=0.6 + 0.4 * ease_out_back(u3), alpha=seg(t, 2.9, 3.15), tag='love')
        ud = seg(t, dur - 0.6, dur)
        if ud > 0: fr.alpha_composite(Image.new('RGBA', (W, H), (90, 60, 50, int(26 * ud))))   # gentle settle, keeps the cream
        return fr
    return render

# ----------------------------------------------------------------------------- timeline
def build():
    tl = Timeline()
    tl.add(4.0, intro(4.0), name='intro p27')
    tl.add(2.7, cake(2.7), trans='circle', tdur=0.4, name='cake p26')
    tl.add(2.7, full(Shot(20, 1.0, 1.12), 2.7, 'Cake time!', 'left', 1500, cap_t=0.55), trans='push_left', tdur=0.4, name='p20')
    tl.add(2.75, full(Shot(21, 1.0, 1.16), 2.75, 'Yummy!', 'right', 1500, cap_t=0.5), trans='slide_over', tdur=0.4, name='p21')
    tl.add(3.3, collage(3.3), trans='push_up', tdur=0.4, name='collage p22+p24')
    tl.add(2.75, full(Shot(23, 1.0, 1.1, p1=(0.03, 0)), 2.75, 'So much love', 'left', 1500), trans='blur', tdur=0.4, name='p23')
    tl.add(3.1, full(Shot(25, 1.05, 1.18), 3.1, 'Mumma & Papa', 'center', 1555, size=60, pink=True), trans='white', tdur=0.4, name='p25')
    tl.add(2.7, full(Shot(28, 1.28, 1.20, focus='all', keep='all', y_bias=0.07), 2.7, 'Sweetest bite', 'right', 1500), trans='slide_up_over', tdur=0.4, name='p28')
    tl.add(3.1, full(Shot(29, 1.0, 1.1, focus=(0.60, 0.5), keep='girl'), 3.1, 'Our sunshine', 'right', 1555, size=52, icon='star'),
           trans='push_right', tdur=0.4, name='p29')
    tl.add(6.1, finale(6.1), trans='white', tdur=0.5, name='finale p30')
    return tl

def ensure_audio():
    if not os.path.exists(AUDIO):
        import importlib.util
        spec = importlib.util.spec_from_file_location('music', os.path.join(SCRATCH, 'music.py'))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        m.make_track(30.7, AUDIO, bpm=104)       # final melody note + closing chord at 28.2 s
    return AUDIO

# ----------------------------------------------------------------------------- QA
def inter(a, b, pad=0):
    return not (a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pad < b[1] or b[3] + pad < a[1])

HAIR_PAD = 60        # px added above her face box (pigtails / hair clips) before the text-vs-face test
CARD_INSET = 12      # px: a face recorded from a card/tile must stay at least this far inside the tile's photo area

def geometry_check(tl):
    """Render every slide alone at 4 local times in probe mode; verify faces inside the frame (and her face inside the safe
    zone), faces from tiles inside their tile (CARD_INSET), text/cards inside the safe zone, and that no text ever touches
    any face (16 px padding; her box is padded HAIR_PAD px upward)."""
    global _PROBE
    ok = True
    st = tl.starts()
    for k, s in enumerate(tl.slides):
        tin = s.tdur if k > 0 else 0.0
        tout = tl.slides[k + 1].tdur if k + 1 < len(tl.slides) else 0.0
        times = sorted(set([round(tin + 0.05, 3), round(s.dur / 2, 3), round(s.dur - tout - 0.05, 3), round(s.dur, 3)]))
        print(f'{s.name:18s} start {st[k]:5.2f}  dur {s.dur:.1f}  clean {s.dur - tin - tout:.2f} s')
        for tt in times:
            _PROBE = []
            try: s.render(tt)
            finally: items, _PROBE = _PROBE, None
            faces_ = [(kind, b, tag) for kind, b, tag in items if kind in ('girl', 'other')]
            cards_ = {tag: b for kind, b, tag in items if kind == 'card'}
            for kind, b, tag in items:
                bb = tuple(int(round(v)) for v in b)
                msgs = []
                if kind in ('girl', 'other'):
                    if bb[0] < 6 or bb[1] < 6 or bb[2] > W - 6 or bb[3] > H - 6: msgs.append('FACE CUT BY FRAME')
                    if kind == 'girl' and not (bb[0] >= SAFE[0] and bb[1] >= SAFE[1] and bb[2] <= SAFE[2] and bb[3] <= SAFE[3]):
                        msgs.append('her face outside safe zone')
                    if kind == 'other' and bb[1] < SAFE[1]: msgs.append('elder face above safe top (warn)')
                    if tag in cards_:                                   # face recorded from a card/tile: must sit inside it
                        cb = cards_[tag]; room = (bb[0] - cb[0], bb[1] - cb[1], cb[2] - bb[2], cb[3] - bb[3])
                        if min(room) < CARD_INSET: msgs.append(f'FACE AT TILE EDGE (room l/t/r/b {tuple(int(v) for v in room)})')
                        elif kind == 'girl' or min(room) < 40: msgs.append(f'tile room l/t/r/b {tuple(int(v) for v in room)}')
                else:
                    if not (bb[0] >= SAFE[0] and bb[1] >= SAFE[1] and bb[2] <= SAFE[2] and bb[3] <= SAFE[3]): msgs.append('OUTSIDE SAFE ZONE')
                    if kind == 'text':
                        for fk, fb, ft in faces_:
                            fbp = (fb[0], fb[1] - (HAIR_PAD if fk == 'girl' else 0), fb[2], fb[3])   # pad upward for her hair / clips
                            if inter(bb, fbp, 16): msgs.append(f'TEXT TOUCHES {fk} FACE+HAIR ({ft})')
                bad = any((m.split(' (')[0].isupper()) or 'outside' in m for m in msgs)
                if bad: ok = False
                if msgs or kind == 'girl':
                    size = f'{bb[2] - bb[0]}x{bb[3] - bb[1]}' if kind in ('girl', 'other') else ''
                    print(f'   {"!!" if bad else "  "} t={tt:5.2f} {kind:5s} {tag:8s} x {bb[0]:4d}-{bb[2]:4d} y {bb[1]:4d}-{bb[3]:4d} {size:9s} {"; ".join(msgs)}')
    print('geometry check', 'OK' if ok else 'HAS ISSUES')
    return ok

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true', help='only write preview sheets')
    ap.add_argument('--check', action='store_true', help='geometry audit (faces / text / cards vs safe zone)')
    ap.add_argument('--snap', type=float, nargs='*', help='half-size frames at these times')
    ap.add_argument('--timing', action='store_true')
    args = ap.parse_args()
    tl = build()
    print('duration %.2f s' % tl.duration)
    for s, st in zip(tl.slides, tl.starts()): print('  %6.2f - %6.2f  %-18s %s %.1f' % (st, st + s.dur, s.name, s.trans, s.tdur))
    if args.check: geometry_check(tl)
    if args.timing:
        for tt in (0.5, 3.7, 5.0, 7.0, 9.5, 12.0, 14.5, 17.0, 19.5, 22.0, 24.0, 27.0, 29.4):
            t0 = time.time(); tl.frame(tt); print('frame %5.2f: %.3f s' % (tt, time.time() - t0))
    if args.snap:
        for tt in args.snap: snap(tl, tt, os.path.join(OUT_DIR, f'{KEY}_snap_{tt:05.2f}.jpg'), scale=0.5)
    if args.preview:
        preview(tl, os.path.join(OUT_DIR, f'{KEY}_prev16.jpg'), n=16, cols=4, scale=0.3)
        st = tl.starts()
        preview(tl, os.path.join(OUT_DIR, f'{KEY}_prev_a.jpg'), n=16, cols=4, scale=0.3,
                times=[0.0, 0.7, 1.5, 2.6, 3.8, 4.7, 5.7, 6.1, 7.3, 8.4, 9.6, 10.7, 12.2, 13.7, 15.0, 16.0])
        preview(tl, os.path.join(OUT_DIR, f'{KEY}_prev_b.jpg'), n=16, cols=4, scale=0.3,
                times=[17.2, 18.7, 19.9, 21.0, 22.3, 23.6, 24.2, 24.9, 25.7, 26.6, 27.6, 28.3, 28.7, 29.1, 29.3, 29.47])
    if args.preview or args.snap or args.timing or args.check: sys.exit(0)
    out = os.path.join(OUT_DIR, f'{KEY}.mp4')
    audio = ensure_audio()
    t0 = time.time()
    encode(tl, out, audio=audio, workers=3, preset='medium', crf=23, audio_fade=0.4)
    print('encode time %.1f s' % (time.time() - t0))
    video_frames_sheet(out, os.path.join(OUT_DIR, f'{KEY}_sheet.jpg'), n=16, cols=4, scale=0.3)
    video_frames_sheet(out, os.path.join(OUT_DIR, f'{KEY}_sheet_big.jpg'), n=8, cols=4, scale=0.5)
