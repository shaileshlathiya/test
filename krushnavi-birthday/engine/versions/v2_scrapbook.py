"""
v2_scrapbook.py - "Pastel Scrapbook" birthday status video for Krushnavi (9:16, 29.5 s).  Round-2 fixed build.

Storyboard (timeline = sum(dur) - sum(tdur) = 29.5 s):
  0.0 - 4.4   Intro: "Happy Birthday" letters bounce in on a common baseline, p11 polaroid ("birthday girl") rises from
              0.55 s, "Krushnavi" (hero, 156 px) bounces in, hearts float behind, 3 stickers stuck on the card
  3.8 - 7.4   Page 1 "Fun days"            p01 ball pit fun / p02 hello elephant! / p08 mirror mirror       (L: hero TL)
  6.8 - 11.2  Page 2 "With Mumma"          p04 with Mumma / p05 Mumma's love / p16 a sweet blessing         (mirrored: hero TR)
 10.6 - 14.2  Page 3 "With Papa"           p06 Papa's girl (landscape hero on top) / p10 Papa & me / p14 little Krishna
 13.6 - 18.0  Page 4 "Festival time"       p03 family time (tall hero, left) / p17 festive look / p09 Ganpati time (column)
 17.4 - 21.0  Page 5 "Out & about"         p12 park day (hero TR) / p13 cheeky smile / p15 shopping day (landscape)
 20.4 - 24.4  Page 6 "Our little princess" p11 cutie pie (small) / p07 so pretty (hero) / p18 sweet smile + "Our sunshine"
 23.6 - 29.5  Finale: heart wipe (p19 polaroid blooms inside the heart), "Happy Birthday" + "Krushnavi!" bounce,
              sign-off writes on, heart burst, slow push-in, fade to cream in step with the music
Transitions: push_left, slide_over, push_stripe (push-down with a mint washi seam), push_up, push_right, slide_up_over, heart_pink.
Fonts: Baloo2 ExtraBold/Bold (headlines), Caveat Bold (hand-written captions).
Palette: cream paper, plum text, pastel pink / mint / lavender / butter / peach accents.
Face sizes (her face width on the 1080x1920 frame, at rest): intro 160, p01 119, p02 71, p08 127, p04 100, p05 83, p16 100,
  p06 110, p10 90, p14 116, p03 82 (Papa 110, Mumma 86), p17 133, p09 75, p12 113, p13 115, p15 113, p11 105, p07 155, p18 133, p19 114.
"""
import sys, os, math, time, subprocess, tempfile, shutil
SCRATCH = os.environ.get('BDAY_DIR') or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # folder holding bday_engine.py, assets/, fonts/
sys.path.insert(0, SCRATCH)
from bday_engine import *
import bday_engine as E

OUT_DIR = os.path.join(SCRATCH, 'out')
KEY = 'v2_scrapbook'
AUDIO = os.path.join(AUDIO_DIR, 'hb_v2_307.wav')     # music.py 30.7 -> final melody note + ending chord at 28.2 s, ringing to 29.5
AUDIO_FADE = (28.9, 0.6)                             # our own afade, same window as the picture's fade to cream

# ----------------------------------------------------------------------------- palette & fonts
PAPER = (253, 247, 238, 255)
PLUM = hexc('#5b3a58')
BROWN = hexc('#6a4a4e')
WHITE = (255, 255, 255, 255)
PINK, PINK_D = hexc('#f8bdd0'), hexc('#ee7fa8')
MINT, MINT_D = hexc('#c3ead9'), hexc('#7fcdb3')
LAV, LAV_D = hexc('#dcd0f5'), hexc('#ab94e3')
BUTTER, BUTTER_D = hexc('#fdeaa6'), hexc('#f4c43f')
PEACH, PEACH_D = hexc('#fdd6c2'), hexc('#f7a27c')

def F_HEAD(s, w='ExtraBold'): return font('Baloo2[wght].ttf', s, w)
def F_CAP(s): return font('Caveat[wght].ttf', s, 'Bold')

def headline(text, size, fill=PLUM, stroke=8, weight='ExtraBold', hard_shadow=None):
    if hard_shadow:   # hard offset shadow (sticker look) instead of the soft one
        return text_layer(text, F_HEAD(size, weight), fill=fill, stroke=stroke, stroke_fill=WHITE,
                          shadow_c=hard_shadow[0], shadow_off=(0, hard_shadow[1]), shadow_blur=0)
    return text_layer(text, F_HEAD(size, weight), fill=fill, stroke=stroke, stroke_fill=WHITE,
                      shadow_c=(91, 58, 88, 70), shadow_off=(0, 8), shadow_blur=10)

# ----------------------------------------------------------------------------- paper backgrounds (built once)
def make_paper(accent, accent2, seed, dots=True):
    r = np.random.default_rng(seed)
    arr = np.empty((H, W, 4), np.uint8)
    arr[:, :, :3] = PAPER[:3]; arr[:, :, 3] = 255
    noise = r.integers(-4, 5, (H, W, 1))
    arr[:, :, :3] = np.clip(arr[:, :, :3].astype(int) + noise, 0, 255).astype(np.uint8)
    bg = Image.fromarray(arr, 'RGBA')
    blob = radial_sprite(1500, with_alpha(accent, 150), power=1.8)
    blob2 = radial_sprite(1300, with_alpha(accent2, 120), power=1.8)
    blit(bg, blob, -150 + r.integers(0, 300), 250 + r.integers(0, 400), alpha=0.6)
    blit(bg, blob2, 1050 + r.integers(0, 200), 1500 + r.integers(0, 300), alpha=0.6)
    if dots:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        hs = heart_sprite(22, with_alpha(accent, 255))
        gy = 0; row = 0
        while gy < H + 100:
            gx = (row % 2) * 48
            while gx < W + 100:
                jx, jy = gx + r.integers(-6, 7), gy + r.integers(-6, 7)
                if (row + gx // 96) % 5 == 2:
                    lay.alpha_composite(hs, (int(jx) - 11, int(jy) - 11))
                else:
                    d.ellipse((jx - 5, jy - 5, jx + 5, jy + 5), fill=with_alpha(accent, 255))
                gx += 96
            gy += 84; row += 1
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * 0.30)))
        bg.alpha_composite(lay)
    return bg

# ----------------------------------------------------------------------------- stickers / tape (built once)
_STK = {}
def sticker(kind, size, color, ow=7):
    """Glossy die-cut sticker with a white outline. kinds: star, heart, flower, circle, balloon, crown, bow, cupcake."""
    k = (kind, size, color, ow)
    if k in _STK: return _STK[k]
    S = size * 2; pad = ow * 2 + 10
    size_px = (S + 2 * pad, S + 2 * pad)
    c = pad + S / 2
    parts = []

    def part(fn, col):
        m = Image.new('L', size_px, 0); fn(ImageDraw.Draw(m)); parts.append((m, col))

    if kind == 'star':
        part(lambda d: d.polygon(star_points(c, c, S / 2 * 0.96, n=5, inner=0.5), fill=255), color)
    elif kind == 'heart':
        part(lambda d: d.polygon([(x + pad, y + pad) for x, y in heart_points(S, S)], fill=255), color)
    elif kind == 'flower':
        def petals_(d):
            pr = S * 0.22
            for q in range(5):
                a = math.radians(-90 + 72 * q); px, py = c + math.cos(a) * S * 0.27, c + math.sin(a) * S * 0.27
                d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=255)
        part(petals_, color)
        rr = S * 0.16
        part(lambda d: d.ellipse((c - rr, c - rr, c + rr, c + rr), fill=255), BUTTER_D)
    elif kind == 'circle':
        part(lambda d: d.ellipse((pad, pad, pad + S, pad + S), fill=255), color)
    elif kind == 'balloon':
        def bal(d):
            d.ellipse((c - 0.34 * S, c - 0.50 * S, c + 0.34 * S, c + 0.26 * S), fill=255)
            d.polygon([(c - 0.07 * S, c + 0.24 * S), (c + 0.07 * S, c + 0.24 * S), (c, c + 0.34 * S)], fill=255)
            pts = [(c + 0.06 * S * math.sin(q / 2.2), c + 0.34 * S + q * 0.016 * S) for q in range(11)]
            d.line(pts, fill=255, width=max(3, int(S * 0.035)))
        part(bal, color)
    elif kind == 'crown':
        def crown(d):
            P = [(-0.44, 0.32), (-0.44, -0.20), (-0.22, 0.04), (0, -0.36), (0.22, 0.04), (0.44, -0.20), (0.44, 0.32)]
            d.polygon([(c + x * S, c + y * S) for x, y in P], fill=255)
            for x, y in ((-0.44, -0.20), (0, -0.36), (0.44, -0.20)):
                r_ = 0.075 * S; d.ellipse((c + x * S - r_, c + y * S - r_, c + x * S + r_, c + y * S + r_), fill=255)
        part(crown, color)
        def gems(d):
            for x in (-0.22, 0, 0.22):
                r_ = 0.055 * S; d.ellipse((c + x * S - r_, c + 0.19 * S - r_, c + x * S + r_, c + 0.19 * S + r_), fill=255)
        part(gems, PINK_D)
    elif kind == 'bow':
        def loops(d):
            d.ellipse((c - 0.50 * S, c - 0.26 * S, c - 0.02 * S, c + 0.12 * S), fill=255)
            d.ellipse((c + 0.02 * S, c - 0.26 * S, c + 0.50 * S, c + 0.12 * S), fill=255)
            d.polygon([(c - 0.04 * S, c + 0.04 * S), (c - 0.34 * S, c + 0.44 * S), (c - 0.12 * S, c + 0.40 * S)], fill=255)
            d.polygon([(c + 0.04 * S, c + 0.04 * S), (c + 0.34 * S, c + 0.44 * S), (c + 0.12 * S, c + 0.40 * S)], fill=255)
        part(loops, color)
        rr = 0.11 * S
        part(lambda d: d.ellipse((c - rr, c - 0.07 * S - rr, c + rr, c - 0.07 * S + rr), fill=255), PLUM if color == LAV_D else PINK_D)
    elif kind == 'cupcake':
        part(lambda d: d.polygon([(c - 0.34 * S, c + 0.02 * S), (c + 0.34 * S, c + 0.02 * S),
                                  (c + 0.25 * S, c + 0.44 * S), (c - 0.25 * S, c + 0.44 * S)], fill=255), color)
        def frosting(d):
            for x, y, r_ in ((-0.21, -0.06, 0.17), (0.21, -0.06, 0.17), (0, -0.18, 0.20), (0, 0.0, 0.18)):
                d.ellipse((c + x * S - r_ * S, c + y * S - r_ * S, c + x * S + r_ * S, c + y * S + r_ * S), fill=255)
        part(frosting, PINK)
        rr = 0.07 * S
        part(lambda d: d.ellipse((c - rr, c - 0.40 * S - rr, c + rr, c - 0.40 * S + rr), fill=255), PINK_D)
    union = parts[0][0].copy()
    for m, _ in parts[1:]: union = ImageChops.lighter(union, m)
    outline = union.filter(ImageFilter.MaxFilter(2 * ow * 2 + 1))
    img = Image.new('RGBA', size_px, (0, 0, 0, 0))
    img.paste(WHITE, mask=outline)
    for m, col in parts: img.paste(col, mask=m)
    hl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse((c - S * 0.30, c - S * 0.36, c - S * 0.05, c - S * 0.14), fill=(255, 255, 255, 110))
    hl = hl.filter(ImageFilter.GaussianBlur(S * 0.05))
    img = Image.alpha_composite(img, apply_mask(hl, union))
    img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    _STK[k] = shadow(img, offset=(0, 5), blur=6, opacity=0.25)      # consistent soft 2-3 px shadow on every sticker
    return _STK[k]

_TAPE = {}
def tape(color, w=190, h=50):
    k = (color, w, h)
    if k in _TAPE: return _TAPE[k]
    S = (w * 2, h * 2)
    m = Image.new('L', S, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, S[0] - 1, S[1] - 1), radius=8, fill=255)
    lay = Image.new('RGBA', S, with_alpha(color, 255))
    st = Image.new('RGBA', S, (0, 0, 0, 0)); d = ImageDraw.Draw(st)
    for x in range(-S[1], S[0] + S[1], 44):
        d.line([(x, 0), (x + S[1], S[1])], fill=(255, 255, 255, 120), width=12)
    lay = Image.alpha_composite(lay, st)
    lay.putalpha(m.point(lambda v: int(v * 0.72)))
    _TAPE[k] = lay.resize((w, h), Image.LANCZOS)
    return _TAPE[k]

def text_sticker(text, accent, size=64, angle=-6, pad_x=44, pad_y=14, fill=PLUM, fnt=None):
    tl = text_layer(text, fnt or F_HEAD(size, 'Bold'), fill=fill)
    pw, ph = tl.width + 2 * pad_x, tl.height + 2 * pad_y
    p = panel(pw, ph, radius=ph // 2, fill=accent)
    p.alpha_composite(tl, ((pw - tl.width) // 2, (ph - tl.height) // 2))
    p = shadow(p, offset=(0, 8), blur=10, opacity=0.18)
    return p.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else p

# ----------------------------------------------------------------------------- polaroid card with washi tape (built once)
CARD_SHADOW = dict(offset=(0, 10), blur=16, opacity=0.35)
CARD_PAD = int(16 * 2 + 10 + 4)        # shadow() padding for CARD_SHADOW
CARD_MARGIN = 80                       # extra margin so rotated tape tips never clip
TAPE_W, TAPE_H = 0.36, 0.085

def card_geometry(w, aspect):
    border = int(w * 0.05); bottom = int(w * 0.22)
    pw = int(w - 2 * border); ph = int(pw / aspect)
    return border, bottom, pw, ph, ph + border + bottom

TAPES_CORNERS = [(0.10, -40, TAPE_W), (0.90, 40, TAPE_W)]     # (x fraction, rotation, width fraction)

def card(i, w, caption, angle, aspect=1.0, zoom=1.15, tape_color=PINK, cap_size=None, focus='girl', keep='auto', y_bias=0.0, tapes=None):
    border, bottom, pw, ph, hh = card_geometry(w, aspect)
    tapes = tapes or TAPES_CORNERS
    pol = polaroid(i, w, caption='', angle=0, zoom=zoom, aspect=aspect, border=border, bottom=bottom,
                   focus=focus, keep=keep, y_bias=y_bias, shadow_kw=CARD_SHADOW)
    cs = cap_size or max(64, int(w * 0.16))
    cap = text_layer(caption, F_CAP(cs), fill=BROWN, shadow_c=(255, 255, 255, 235), shadow_off=(0, 0), shadow_blur=3)
    blit(pol, cap, CARD_PAD + w / 2, CARD_PAD + ph + border + bottom / 2 + 2)
    M = CARD_MARGIN
    lay = Image.new('RGBA', (pol.width + 2 * M, pol.height + 2 * M), (0, 0, 0, 0))
    lay.alpha_composite(pol, (M, M))
    for tx, rot, wf in tapes:
        blit(lay, tape(tape_color, int(w * wf), int(w * TAPE_H)), M + CARD_PAD + w * tx, M + CARD_PAD + 4, rot=rot)
    if angle: lay = lay.rotate(angle, resample=Image.BICUBIC, expand=True)
    return lay

def ground_shadow(lay):
    """soft shadow of a card's paper (alpha>=150) used while the card lifts off the page."""
    a = lay.getchannel('A').point(lambda v: 255 if v >= 150 else 0)
    sh = Image.new('RGBA', lay.size, (0, 0, 0, 0)); sh.putalpha(a)
    return sh.filter(ImageFilter.GaussianBlur(22))

def faces_in_card(i, w, aspect, zoom, focus='girl', keep='auto', y_bias=0.0):
    """Face boxes ([girl] + others) and the photo rect in card (paper) coordinates - QA helper mirroring fit()."""
    border, bottom, pw, ph, hh = card_geometry(w, aspect)
    img = photo(i); sw, sh = img.size
    fp = focus_point(i, focus); fp = (fp[0], fp[1] + y_bias)
    if keep == 'auto': kp = faces(i, 'all') if zoom <= 1.3 else faces(i, 'girl')
    elif keep == 'girl': kp = faces(i, 'girl')
    elif keep == 'all': kp = faces(i, 'all')
    else: kp = keep
    box = cover_box(img, pw, ph, fp, zoom, (0, 0), kp)
    sx = pw / (box[2] - box[0]); sy = ph / (box[3] - box[1])
    out = [(border + (g[0] * sw - box[0]) * sx, border + (g[1] * sh - box[1]) * sy,
            border + (g[2] * sw - box[0]) * sx, border + (g[3] * sh - box[1]) * sy) for g in faces(i, 'all')]
    return out, (border, border, border + pw, border + ph), (keep == 'all' or (keep == 'auto' and zoom <= 1.3))

# ----------------------------------------------------------------------------- page definitions
# card layout tuples: (photo, caption, cx, cy, w, aspect, angle, zoom, extra-kwargs); draw order = list order.
# stickers: (kind, colour, cx, cy, size, angle) - each one is stuck on a card corner / edge or on the title pill.
ALL = dict(focus='all', keep='all')
PAGES = [
    dict(title='Fun days', side=+1, accent=BUTTER, accent_d=BUTTER_D, wash2=MINT, motion='drop', seed=11, tape=PINK, dur=3.6,
         cards=[('p01', 'ball pit fun', 330, 730, 440, 1.0, -6, 1.25, {}),
                ('p02', 'hello elephant!', 750, 985, 400, 0.85, 5, 2.2, dict(y_bias=0.08)),
                ('p08', 'mirror mirror', 335, 1335, 440, 1.0, -3, 1.6, dict(keep='girl'))],
         stickers=[('star', BUTTER_D, 556, 488, 92, 12), ('balloon', PINK_D, 860, 1430, 112, -8)], bump=0),
    dict(title='With Mumma', side=-1, accent=PINK, accent_d=PINK_D, wash2=LAV, motion='slide', seed=12, tape=MINT, dur=4.4,
         cards=[('p04', 'with Mumma', 718, 790, 480, 0.85, -3, 1.55, dict(ALL)),
                ('p05', "Mumma's love", 320, 745, 400, 1.0, 5, 1.65, dict(ALL, y_bias=0.06)),
                ('p16', 'a sweet blessing', 520, 1393, 420, 1.3, 4, 1.2, dict(ALL, y_bias=0.12, tapes=[(0.52, -6, 0.20)]))],
         stickers=[('heart', PINK_D, 525, 458, 96, 8), ('bow', LAV_D, 628, 348, 104, -12)], bump=1),
    dict(title='With Papa', side=+1, accent=MINT, accent_d=MINT_D, wash2=BUTTER, motion='pop', seed=13, tape=LAV, dur=3.6,
         cards=[('p06', "Papa's girl", 560, 794, 620, 1.45, 2, 1.55, dict(ALL, y_bias=0.04, cap_size=84)),
                ('p10', 'Papa & me', 320, 1366, 380, 1.0, 3, 1.7, dict(ALL, y_bias=0.05)),
                ('p14', 'little Krishna', 760, 1366, 380, 1.0, -4, 1.5, dict(ALL, y_bias=0.04))],
         stickers=[('star', BUTTER_D, 862, 530, 90, 15), ('balloon', MINT_D, 505, 368, 104, 10)], bump=0),
    dict(title='Festival time', side=-1, accent=LAV, accent_d=LAV_D, wash2=PEACH, motion='rise', seed=14, tape=BUTTER, dur=4.4,
         cards=[('p03', 'family time', 345, 1000, 480, 0.75, -4, 2.1, dict(ALL, y_bias=0.02)),
                ('p17', 'festive look', 765, 712, 420, 1.0, 4, 1.6, dict(y_bias=0.05)),
                ('p09', 'Ganpati time', 738, 1290, 440, 0.8, -3, 1.9, dict(ALL, y_bias=0.03))],
         stickers=[('flower', PINK_D, 142, 662, 100, 0), ('star', BUTTER_D, 562, 968, 90, 12)], bump=1),
    dict(title='Out & about', side=+1, accent=BUTTER, accent_d=BUTTER_D, wash2=PINK, motion='slide', seed=15, tape=LAV, dur=3.6,
         cards=[('p12', 'park day', 728, 744, 460, 1.0, -4, 1.7, dict(y_bias=0.07)),
                ('p13', 'cheeky smile', 330, 1010, 420, 0.8, 4, 1.7, dict(y_bias=0.10)),
                ('p15', 'shopping day', 760, 1380, 440, 1.3, 3, 1.4, dict(y_bias=0.07))],
         stickers=[('cupcake', BUTTER_D, 455, 368, 104, -8), ('heart', PINK_D, 560, 1120, 86, 12)], bump=1),
    dict(title='Our little princess', side=-1, accent=PINK, accent_d=PINK_D, wash2=MINT, motion='spin', seed=16, tape=BUTTER, dur=4.0,
         cards=[('p11', 'cutie pie', 262, 790, 300, 1.0, -6, 1.3, {}),
                ('p07', 'so pretty', 700, 820, 520, 1.0, 3, 1.8, dict(y_bias=0.11)),
                ('p18', 'sweet smile', 312, 1356, 400, 1.0, -3, 1.6, dict(y_bias=0.08))],
         stickers=[('crown', BUTTER_D, 930, 520, 104, 10), ('heart', PINK_D, 445, 790, 84, -12)], bump=2,
         text=('Our sunshine', LAV, 690, 1300, -8)),
]
TRANS = ['push_left', 'slide_over', 'push_stripe', 'push_up', 'push_right', 'slide_up_over']
INTRO_DUR, FINALE_DUR, TDUR, FIN_TDUR = 4.4, 5.9, 0.6, 0.8
EXIT_TITLE = {5: FIN_TDUR}   # page whose title slides out before the blending heart wipe
INTRO_CARD_Y = 1236
SAFE = (72, 262, 1008, 1618)

# ----------------------------------------------------------------------------- custom transitions
def tr_push_stripe(a, b, p):
    """Push-down (new page slides in from the top) with a mint washi seam - no face is ever cut by a wipe edge."""
    e = ease_in_out_cubic(p)
    oy = int(H * e)
    out = Image.new('RGBA', (W, H), PAPER)
    out.paste(a, (0, oy)); out.paste(b, (0, oy - H))
    if 0 < p < 1:
        ol = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ol)
        d.line([(-10, oy), (W + 10, oy)], fill=MINT_D, width=30)
        d.line([(-10, oy), (W + 10, oy)], fill=(255, 255, 255, 200), width=8)
        out.alpha_composite(ol)
    return out

def tr_heart_pink(a, b, p):
    """Heart wipe with a pink outline (fades out on its own layer) and a pink flash inside, dilating to full at the end."""
    e = ease_in_out(p); s = int(e * H * 1.6 + 4)
    m = Image.new('L', (W, H), 0)
    hp = [(x - s / 2 + W / 2, y - s / 2 + H / 2) for x, y in heart_points(s, s)]
    ImageDraw.Draw(m).polygon(hp, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(6))
    tail = ease_in_out(seg(p, 0.82, 1.0))
    if tail > 0: m = ImageChops.lighter(m, Image.new('L', (W, H), int(255 * tail)))
    bt = b
    fl = 0.38 * (1 - p)
    if fl > 0.01: bt = Image.alpha_composite(b, Image.new('RGBA', b.size, with_alpha(PINK, int(255 * fl))))
    out = Image.composite(bt, a, m)
    if 0 < p < 0.95:
        ol = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ol)
        al = 1 - ease_in_out_sine(seg(p, 0.64, 0.95))     # ~8 frames of gradual fade while the mask dilates
        d.line(hp + [hp[0]], fill=with_alpha(PINK_D, int(255 * al)), width=28, joint='curve')
        d.line(hp + [hp[0]], fill=(255, 255, 255, int(210 * al)), width=8, joint='curve')
        out.alpha_composite(ol)
    return out

E.TRANSITIONS['push_stripe'] = tr_push_stripe
E.TRANSITIONS['heart_pink'] = tr_heart_pink

# ----------------------------------------------------------------------------- soft petals (behind the cards)
def petal_sprite(size, color, heart=False):
    S = size * 2
    s = Image.new('RGBA', (S + 8, S + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    if heart: d.polygon([(x + 4, y + 4) for x, y in heart_points(S, S)], fill=color)
    else: d.ellipse((4, 4 + S * 0.2, 4 + S, 4 + S * 0.8), fill=color)
    s = s.filter(ImageFilter.GaussianBlur(2.5))
    return s.resize((s.width // 2, s.height // 2), Image.LANCZOS)

class Petals:
    def __init__(self, colors, n=13, seed=1, size=(28, 52), alpha=0.6, t_off=3.0):
        r = np.random.default_rng(seed); self.n, self.alpha, self.t_off = n, alpha, t_off
        self.x = r.uniform(0, W, n); self.y = r.uniform(0, H, n); self.sz = r.uniform(size[0], size[1], n)
        self.sp = r.uniform(45, 95, n); self.ph = r.uniform(0, 6.28, n); self.fr = r.uniform(0.5, 1.2, n)
        self.rot = r.uniform(0, 360, n); self.rs = r.uniform(-40, 40, n)
        self.spr = [petal_sprite(int(s), colors[j % len(colors)], heart=(j % 3 == 2)) for j, s in enumerate(self.sz)]
    def draw(self, fr, t):
        t = t + self.t_off
        for j in range(self.n):
            y = (self.y[j] + self.sp[j] * t) % (H + 120) - 60
            x = (self.x[j] + 40 * math.sin(t * self.fr[j] + self.ph[j])) % (W + 100) - 50
            blit(fr, self.spr[j], x, y, rot=self.rot[j] + self.rs[j] * t, alpha=self.alpha)

# ----------------------------------------------------------------------------- build all static layers once
t_build = time.time()
BG = {}
BG['intro'] = make_paper(PINK, LAV, 1)
BG['finale'] = make_paper(LAV, PINK, 2)
for k, pg in enumerate(PAGES):
    BG[k] = make_paper(pg['accent'], pg['wash2'], 10 + k)
CREAM = Image.new('RGBA', (W, H), PAPER)

def vis_bbox(layer, thr=150):
    a = np.asarray(layer.getchannel('A')); ys, xs = np.where(a >= thr)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())

TITLE_Y = 334
PAGE_LAYERS = []
for k, pg in enumerate(PAGES):
    cards = [card(c[0], c[4], c[1], c[6], aspect=c[5], zoom=c[7], tape_color=pg['tape'], **c[8]) for c in pg['cards']]
    stks = [sticker(s[0], s[4], s[1]) for s in pg['stickers']]
    title = text_sticker(pg['title'], pg['accent'], size=72, angle=-3 * pg['side'], pad_x=48, pad_y=10)
    tb_ = vis_bbox(title, 100)
    off = min(190, (SAFE[2] - SAFE[0] - (tb_[2] - tb_[0])) // 2 - 16)
    title_cx = 540 + pg['side'] * off
    txt = text_sticker(pg['text'][0], pg['text'][1], size=54, angle=pg['text'][4], pad_x=36, pad_y=10) if pg.get('text') else None
    petals = Petals([pg['accent_d'], PINK_D, LAV_D, MINT_D], n=13, seed=pg['seed'], t_off=4.0 + k)
    PAGE_LAYERS.append(dict(cards=cards, stickers=stks, title=title, title_cx=title_cx, text=txt, petals=petals,
                            gshadow=ground_shadow(cards[pg['bump']])))

# intro layers: letters on a common baseline (layer, cx, baseline, centre offset from baseline)
INTRO_WORDS = []
LETTER_SIZE = 132
for word, base in (('Happy', 422), ('Birthday', 566)):
    fnt = F_HEAD(LETTER_SIZE); gap = 6; asc = fnt.getmetrics()[0]
    widths = [fnt.getlength(ch) for ch in word]
    total = sum(widths) + gap * (len(word) - 1)
    x = W / 2 - total / 2; letters = []
    for ch, wd in zip(word, widths):
        bb = fnt.getbbox(ch, stroke_width=8)
        letters.append((headline(ch, LETTER_SIZE), x + wd / 2, base, (bb[1] + bb[3]) / 2 - asc)); x += wd + gap
    INTRO_WORDS.append(letters)
INTRO_NAME = headline('Krushnavi', 156, fill=PINK_D, stroke=9, hard_shadow=(PLUM, 6))
INTRO_CARD_SPEC = ('p11', 560, 'birthday girl', -4, 0.9, 1.06, 86)
INTRO_CARD = card('p11', 560, 'birthday girl', -4, aspect=0.9, zoom=1.06, tape_color=PINK, cap_size=86)
# stickers stuck on the intro card: star on the top-right corner, balloon on the left edge, heart on the bottom-right corner
INTRO_STK = [(sticker('star', 96, BUTTER_D), 812, 898, 14), (sticker('balloon', 116, PINK_D), 250, 1180, -8),
             (sticker('heart', 84, LAV_D), 800, 1552, -12)]
INTRO_HEARTS = Particles('heart', n=14, seed=4, colors=[PINK, PINK_D, LAV, PEACH_D], size=(36, 84), speed=(70, 130), sway=30, alpha=0.85, t_offset=5.0)

# finale layers
FIN_CARD_SPEC = ('p19', 600, 'hugs & kisses', 3, 0.95, 1.06, 84)
FIN_CARD = card('p19', 600, 'hugs & kisses', 3, aspect=0.95, zoom=1.06, tape_color=MINT, cap_size=84)
FIN_T1 = headline('Happy Birthday', 104)
FIN_T2 = headline('Krushnavi!', 164, fill=PINK_D, stroke=9, hard_shadow=(PLUM, 6))
FIN_T3 = text_layer('Lots of love, Mumma & Papa', F_CAP(80), fill=PLUM, shadow_c=(255, 255, 255, 220), shadow_off=(0, 0), shadow_blur=5)
FIN_SIDE = Particles('heart', n=9, seed=21, colors=[PINK_D, PINK, LAV_D, PEACH_D], size=(34, 70), speed=(90, 160), sway=22, alpha=0.9, t_offset=3.0, area=(170, H))
FIN_SIDE2 = Particles('heart', n=9, seed=22, colors=[PINK_D, PINK, LAV_D, MINT_D], size=(34, 70), speed=(90, 160), sway=22, alpha=0.9, t_offset=3.0, area=(170, H))
FIN_SPARK = Particles('sparkle', n=14, seed=23, size=(30, 50), alpha=0.9, colors=[hexc('#ffd166'), hexc('#ff9ecd'), hexc('#ffe9a8')])
_r = np.random.default_rng(7)
BURST = [(math.radians(a + _r.uniform(-8, 8)), _r.uniform(400, 600), heart_sprite(int(_r.uniform(50, 90)), [PINK_D, LAV_D, PEACH_D, MINT_D][j % 4]), _r.uniform(0, 0.3))
         for j, a in enumerate(range(0, 360, 20))]
print('[build] static layers in %.1fs' % (time.time() - t_build))

# ----------------------------------------------------------------------------- motion helpers
def wobble(t, te, amp=3.0):
    d = t - te
    if d <= 0 or d > 1.1: return 0.0
    return amp * math.exp(-4.0 * d) * math.sin(14.0 * d)

def enter(t, t0, dur, motion, cx, cy, k):
    """(x, y, scale, alpha, rot) for a card entering with the given motion (soft overshoot)."""
    u = seg(t, t0, t0 + dur)
    if u <= 0: return None
    ec = ease_out_cubic(u)
    x, y, sc, al, rot = cx, cy, 1.0, 1.0, 0.0
    if motion == 'drop':
        e = ease_out_back(u, 0.6)
        if cy > 1000: y = cy + (1 - e) * 1100
        else: y = cy - (1 - e) * (cy + 700)
        rot = (1 - ec) * (-10 if k % 2 == 0 else 10)
    elif motion == 'slide':
        e = ease_out_back(u, 0.7)
        side = -1 if cx < 540 else 1                 # cards come in from their own side
        x = cx + side * (1 - e) * (W * 0.75 + 300); rot = (1 - ec) * side * 6
    elif motion == 'pop':
        e = ease_out_back(u, 1.4)
        sc = 0.35 + 0.65 * e; al = clamp01(u * 2.5)
    elif motion == 'rise':
        e = ease_out_back(u, 0.6)
        y = cy + (1 - e) * 1100; rot = (1 - ec) * (8 if k % 2 == 0 else -8)
    elif motion == 'spin':
        e = ease_out_back(u, 1.4)
        sc = 0.3 + 0.7 * e; al = clamp01(u * 2.5); rot = (1 - ec) * (-28 if k % 2 == 0 else 28)
    rot += wobble(t, t0 + dur, 2.2 if motion in ('drop', 'rise') else 1.4)
    return x, y, sc, al, rot

def draw_sticker(fr, spr, s, t, t0, j, beat=False):
    kind, col, cx, cy, size, ang = s
    u = seg(t, t0, t0 + 0.5)
    if u <= 0: return
    if beat:      # the beat sticker: 25 % overshoot and a decaying 10 deg wiggle
        sc = ease_out_back(u, 3.0); wig = 10 * math.sin(2 * math.pi * 1.5 * u) * (1 - u)
    else:
        sc = ease_out_back(u, 2.0); wig = 0.0
    sway = 4 * math.sin(2 * math.pi * t / 2.4 + j * 1.3)
    blit(fr, spr, cx, cy, scale=max(0.02, sc) * (1 + 0.03 * math.sin(2 * math.pi * t / 1.9 + j)), rot=ang + sway + wig)

# ----------------------------------------------------------------------------- slides
def intro(t):
    fr = BG['intro'].copy()
    INTRO_HEARTS.draw(fr, t)
    i = 0
    for letters in INTRO_WORDS:
        for lay, cx, base, off in letters:
            u = seg(t, 0.1 + i * 0.07, 0.1 + i * 0.07 + 0.55)
            if u > 0:
                sc = ease_out_back(u, 1.7)
                dy = -(1 - ease_out_cubic(u)) * 40 + 4 * math.sin(2 * math.pi * t / 2.2 + i * 0.5)
                blit(fr, lay, cx, base + sc * off + dy, scale=max(0.02, sc), alpha=clamp01(u * 3))
            i += 1
    # polaroid is already in place on frame 0 (status apps use the first frame as the thumbnail),
    # with a soft settle (scale 1.06 -> 1.0, rot 4 -> 0) over the first 0.7 s; stays under the name
    us = ease_out_cubic(seg(t, 0.0, 0.7))
    y = INTRO_CARD_Y + 5 * math.sin(2 * math.pi * t / 2.8)
    rot = (1 - us) * 4 + wobble(t, 1.5, 2.2)
    blit(fr, INTRO_CARD, 540, y, scale=1 + 0.06 * (1 - us), rot=rot)
    # her name - the hero of the opening
    u = seg(t, 1.45, 2.05)
    if u > 0:
        sc = ease_out_back(u, 1.6)
        blit(fr, INTRO_NAME, 540, 686 + 3 * math.sin(2 * math.pi * t / 2.6),
             scale=max(0.02, sc) * (1 + 0.012 * math.sin(2 * math.pi * t / 1.6)), alpha=clamp01(u * 3))
    for j, (spr, cx, cy, ang) in enumerate(INTRO_STK):
        u = seg(t, 2.0 + j * 0.2, 2.5 + j * 0.2)
        if u > 0:
            blit(fr, spr, cx, cy, scale=max(0.02, ease_out_back(u, 2.0)) * (1 + 0.03 * math.sin(2 * math.pi * t / 1.9 + j)),
                 rot=ang + 4 * math.sin(2 * math.pi * t / 2.4 + j))
    return fr

def make_page(k):
    pg = PAGES[k]; L = PAGE_LAYERS[k]
    motion = pg['motion']; n = len(pg['cards']); dur = pg['dur']
    tb = dur * 0.55                      # mid-page beat
    exit_t = EXIT_TITLE.get(k); bump = pg['bump']; tcx = L['title_cx']
    def render(t):
        fr = BG[k].copy()
        L['petals'].draw(fr, t)
        ub = seg(t, tb, tb + 0.55)
        lift = math.sin(math.pi * ease_in_out_sine(ub)) if 0 < ub < 1 else 0.0
        for j, c in enumerate(pg['cards']):
            _, _, cx, cy, w, aspect, ang, _, _ = c
            st = enter(t, 0.1 + j * 0.24, 0.65, motion, cx, cy, j)
            if st is None: continue
            x, y, sc, al, rot = st
            y += 5 * math.sin(2 * math.pi * t / 2.7 + j * 2.0)
            if j == bump and lift > 0:   # the beat: card lifts 60 px off the page, tilts 4 deg, its shadow stays behind
                blit(fr, L['gshadow'], x, y + 14 + 14 * lift, alpha=0.5 * lift)
                y -= 60 * lift; rot += 4.0 * lift * (1 if j % 2 == 0 else -1)
            blit(fr, L['cards'][j], x, y, scale=max(0.02, sc), alpha=al, rot=rot if abs(rot) > 0.05 else 0.0)
        if L['text'] is not None:
            tx = pg['text']; u = seg(t, 0.1 + n * 0.24, 0.1 + n * 0.24 + 0.6)
            if u > 0:
                blit(fr, L['text'], tx[2], tx[3] + 4 * math.sin(2 * math.pi * t / 2.3), scale=max(0.02, ease_out_back(u, 1.8)), alpha=clamp01(u * 3))
        # title pill (offset to one side, tilted): drops in on top of the cards; slides out before a blending transition
        u = seg(t, 0.0, 0.6)
        if u > 0:
            e = ease_out_back(u, 1.5); ty = TITLE_Y - (1 - e) * 260; ta = clamp01(u * 3)
            if exit_t is not None:
                ux = seg(t, dur - exit_t, dur - exit_t + 0.3)
                if ux > 0: ty = TITLE_Y - ease_in_cubic(ux) * 300; ta = 1 - ux
            if ta > 0: blit(fr, L['title'], tcx, ty, alpha=ta)
        # stickers are stuck on top of everything (card corners / the pill)
        draw_sticker(fr, L['stickers'][0], pg['stickers'][0], t, 0.1 + n * 0.24 + 0.3, 0)
        draw_sticker(fr, L['stickers'][1], pg['stickers'][1], t, tb, 1, beat=True)
        return fr
    return render

FIN_CARD_Y = 1075
def finale(t):
    fr = BG['finale'].copy()
    strip = Image.new('RGBA', (170, H), (0, 0, 0, 0)); FIN_SIDE.draw(strip, t); fr.alpha_composite(strip, (50, 0))
    strip = Image.new('RGBA', (170, H), (0, 0, 0, 0)); FIN_SIDE2.draw(strip, t); fr.alpha_composite(strip, (860, 0))
    if 1.7 < t < 3.5:
        for ang, rad, spr, dl in BURST:
            uu = seg(t, 1.7 + dl, 3.1 + dl)
            if uu <= 0 or uu >= 1: continue
            e = ease_out_cubic(uu)
            blit(fr, spr, 540 + math.cos(ang) * rad * e, FIN_CARD_Y + math.sin(ang) * rad * e * 0.9, scale=0.5 + 0.6 * e, alpha=1 - uu ** 2)
    # polaroid blooms inside the heart while the wipe completes, then a slow push-in
    u = seg(t, 0.5, 1.4)
    if u > 0:
        e = ease_out_back(u, 1.3)
        push = 1 + 0.03 * ease_in_out_sine(seg(t, 2.9, FINALE_DUR))
        blit(fr, FIN_CARD, 540, FIN_CARD_Y + 5 * math.sin(2 * math.pi * t / 2.9), scale=max(0.02, 0.3 + 0.7 * e) * push, alpha=clamp01(u * 2.5),
             rot=(1 - ease_out_cubic(u)) * 18 + wobble(t, 1.4, 1.5))
    u = seg(t, 1.15, 1.75)
    if u > 0:
        e = ease_out_back(u, 1.5)
        blit(fr, FIN_T1, 540, 352 - (1 - e) * 220, alpha=clamp01(u * 3))
    u = seg(t, 1.55, 2.25)
    if u > 0:
        sc = ease_out_back(u, 1.9)
        blit(fr, FIN_T2, 540, 500 + 3 * math.sin(2 * math.pi * t / 2.1), scale=max(0.02, sc) * (1 + 0.015 * math.sin(2 * math.pi * t / 1.4)), alpha=clamp01(u * 3))
    u = seg(t, 2.5, 3.4)
    if u > 0:
        blit(fr, reveal(FIN_T3, ease_in_out_sine(u), 'lr', soft=90), 540, 1532)
    if t > 1.2: FIN_SPARK.draw(fr, t)
    uf = seg(t, FINALE_DUR - 0.6, FINALE_DUR)          # 28.9-29.5 s, same window as the audio fade
    if uf > 0: fr = Image.blend(fr, CREAM, 0.72 * ease_in_out_sine(uf))   # keep the card faintly visible on the last frame
    return fr

# ----------------------------------------------------------------------------- timeline
def build():
    tl = Timeline()
    tl.add(INTRO_DUR, intro, name='intro')
    for k in range(len(PAGES)):
        tl.add(PAGES[k]['dur'], make_page(k), trans=TRANS[k], tdur=TDUR, name=PAGES[k]['title'])
    tl.add(FINALE_DUR, finale, trans='heart_pink', tdur=FIN_TDUR, name='finale')
    return tl

tl = build()

# ----------------------------------------------------------------------------- encode with our own audio fade
def encode_with_audio(tl, out, wav, fade_st, fade_d):
    tmpd = tempfile.mkdtemp(prefix='v2mux_'); silent = os.path.join(tmpd, 'silent.mp4')
    encode(tl, silent, audio=None, workers=3, preset='medium', crf=19)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', silent, '-i', wav, '-map', '0:v:0', '-map', '1:a:0',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-af', f'afade=t=out:st={fade_st}:d={fade_d}',
                    '-shortest', '-movflags', '+faststart', out], check=True)
    shutil.rmtree(tmpd, ignore_errors=True)
    return out

# ----------------------------------------------------------------------------- QA: mask-based layout check
def card_annot(i, w, caption, angle, aspect=1.0, zoom=1.15, cap_size=None, focus='girl', keep='auto', y_bias=0.0, tapes=None):
    """L masks (girl face, other faces, caption text, tapes) in the card layer's geometry, dilated 10 px, rotated like the card."""
    border, bottom, pw, ph, hh = card_geometry(w, aspect)
    O = CARD_MARGIN + CARD_PAD
    lw, lh = int(w) + 2 * O, hh + 2 * O
    boxes, prect, others_kept = faces_in_card(i, w, aspect, zoom, focus, keep, y_bias)
    def clip(b): return (max(b[0], prect[0]), max(b[1], prect[1]), min(b[2], prect[2]), min(b[3], prect[3]))
    def rect_mask(bs):
        m = Image.new('L', (lw, lh), 0); d = ImageDraw.Draw(m)
        for b in bs:
            b = clip(b)
            if b[2] > b[0] and b[3] > b[1]: d.rectangle((O + b[0], O + b[1], O + b[2], O + b[3]), fill=255)
        return m
    girl = rect_mask([boxes[0]]); others = rect_mask(boxes[1:])
    cut = [not (prect[0] <= b[0] and prect[1] <= b[1] and b[2] <= prect[2] and b[3] <= prect[3]) for b in boxes[1:]]
    cs = cap_size or max(64, int(w * 0.16))
    capl = text_layer(caption, F_CAP(cs), fill=BROWN); cb = vis_bbox(capl, 100)
    ccx, ccy = O + w / 2, O + ph + border + bottom / 2 + 2
    cap = Image.new('L', (lw, lh), 0)
    ImageDraw.Draw(cap).rectangle((ccx - capl.width / 2 + cb[0], ccy - capl.height / 2 + cb[1], ccx - capl.width / 2 + cb[2], ccy - capl.height / 2 + cb[3]), fill=255)
    tapes_m = Image.new('L', (lw, lh), 0)
    for tx, rot, wf in (tapes or TAPES_CORNERS):
        r_ = Image.new('L', (int(w * wf), int(w * TAPE_H)), 255).rotate(rot, expand=True)
        tapes_m.paste(r_, (int(round(O + w * tx - r_.width / 2)), int(round(O + 4 - r_.height / 2))), r_)
    tapes = tapes_m
    girl, others, cap = [m.filter(ImageFilter.MaxFilter(21)) for m in (girl, others, cap)]
    if angle: girl, others, cap, tapes = [m.rotate(angle, expand=True) for m in (girl, others, cap, tapes)]
    g = boxes[0]
    return dict(girl=girl, others=others, cap=cap, tapes=tapes, face_px=(g[2] - g[0], g[3] - g[1]),
                others_px=[(b[2] - b[0]) for b in boxes[1:]], others_kept=others_kept, others_cut=cut)

def place(layer_or_mask, cx, cy, scale=1.0, thr=None, rot=0.0):
    """Frame-size L mask of a layer (alpha >= thr) or an L mask, placed like blit()."""
    lay = layer_or_mask
    if thr is not None: lay = lay.getchannel('A').point(lambda v: 255 if v >= thr else 0)
    if abs(scale - 1) > 1e-3: lay = lay.resize((max(1, int(round(lay.width * scale))), max(1, int(round(lay.height * scale)))), Image.NEAREST)
    if rot: lay = lay.rotate(rot, expand=True)
    m = Image.new('L', (W, H), 0)
    m.paste(lay, (int(round(cx - lay.width / 2)), int(round(cy - lay.height / 2))))
    return m

def inter(a, b):
    return int(np.count_nonzero(np.logical_and(np.asarray(a) > 127, np.asarray(b) > 127)))

def mbbox(m):
    ys, xs = np.where(np.asarray(m) > 127)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None

def layout_check(save_sheet=True):
    ok = True; tiles = []
    def chk(name, bb):
        nonlocal ok
        if bb is None: return
        bad = bb[0] < SAFE[0] or bb[1] < SAFE[1] or bb[2] > SAFE[2] or bb[3] > SAFE[3]
        print(('  !! ' if bad else '     ') + f'{name:30s} x {bb[0]:4d}-{bb[2]:4d}  y {bb[1]:4d}-{bb[3]:4d}')
        ok = ok and not bad
    def fail(msg):
        nonlocal ok
        print('  !! ' + msg); ok = False
    for k, pg in enumerate(PAGES):
        print(f'page {k} {pg["title"]}  (motion {pg["motion"]})')
        L = PAGE_LAYERS[k]; motion = pg['motion']
        title_m = place(L['title'], L['title_cx'], TITLE_Y, thr=100); chk('title', mbbox(title_m))
        items = []    # per card: dict(vis, vis_os, girl, others, cap, tapes)
        for j, c in enumerate(pg['cards']):
            pid, capt, cx, cy, w, aspect, ang, zoom, kw = c
            lay = L['cards'][j]; an = card_annot(pid, w, capt, ang, aspect=aspect, zoom=zoom, **kw)
            vis = place(lay, cx, cy, thr=150)
            if motion in ('pop', 'spin'): vis_os = ImageChops.lighter(vis, place(lay, cx, cy, scale=1.06, thr=150))
            elif motion == 'slide': vis_os = ImageChops.lighter(vis, place(lay, cx + (22 if cx < 540 else -22), cy, thr=150))
            elif motion == 'drop': vis_os = ImageChops.lighter(vis, place(lay, cx, cy + (-16 if cy > 1000 else 16), thr=150))
            else: vis_os = ImageChops.lighter(vis, place(lay, cx, cy - 16, thr=150))
            d = dict(vis=vis, vis_os=vis_os, pid=pid, capt=capt, cx=cx, cy=cy, lay=lay, an=an)
            for key_ in ('girl', 'others', 'cap', 'tapes'): d[key_] = place(an[key_], cx, cy)
            items.append(d)
            fw, fh = an['face_px']
            chk(f'{pid} {capt}', mbbox(vis))
            print(f'        face {fw:5.0f}x{fh:5.0f} px' + (f'  others {[int(v) for v in an["others_px"]]}' if an['others_px'] else '')
                  + ('  kept' if an['others_kept'] else '') + ('  OTHERS CUT ' + str(an['others_cut']) if an['others_kept'] and any(an['others_cut']) else ''))
            if an['others_kept'] and any(an['others_cut']): fail(f'{pid}: a kept parent face is cut by the crop')
            if inter(d['tapes'], d['girl']): fail(f'{pid}: own tape touches her face')
            if inter(title_m, vis_os): fail(f'{pid}: title pill overlaps the card (incl. overshoot)')
            for i_ in range(j):
                p = items[i_]
                for nm in ('girl', 'others', 'cap'):
                    n_ = inter(vis_os, p[nm])
                    if n_: fail(f'{pid} covers {p["pid"]} {nm} ({n_} px)')
        fmax = max(it['an']['face_px'][0] for it in items); fmin = min(it['an']['face_px'][0] for it in items)
        if fmax < 90: fail(f'largest face on the page only {fmax:.0f} px (< 90)')
        if fmin < 65: fail(f'smallest face on the page only {fmin:.0f} px (< 65)')
        stk_masks = []
        for s_i, s in enumerate(pg['stickers']):
            sm = place(L['stickers'][s_i], s[2], s[3], scale=1.3 if s_i == 1 else 1.15, thr=100, rot=s[5])
            chk(f'sticker {s[0]}', mbbox(sm)); stk_masks.append(sm)
            touch = [it['pid'] for it in items if inter(sm, it['vis'])]
            if not touch: print(f'        ({s[0]} is free-floating)')
            for it in items:
                for nm in ('girl', 'others', 'cap'):
                    n_ = inter(sm, it[nm])
                    if n_: fail(f'sticker {s[0]} covers {it["pid"]} {nm} ({n_} px)')
        if L['text'] is not None:
            tx = pg['text']; tm = place(L['text'], tx[2], tx[3], scale=1.08, thr=100); chk('text sticker', mbbox(tm))
            for it in items:
                for nm in ('girl', 'others', 'cap'):
                    n_ = inter(tm, it[nm])
                    if n_: fail(f'text sticker covers {it["pid"]} {nm} ({n_} px)')
        if save_sheet:
            st = tl.starts()[k + 1]
            fr = tl.frame(st + 1.7).convert('RGB')
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            for it in items:
                for nm, col in (('girl', (255, 0, 0, 90)), ('others', (0, 200, 0, 90)), ('cap', (0, 80, 255, 90)), ('tapes', (255, 200, 0, 70))):
                    ov.paste(col, mask=it[nm])
            ov.paste((255, 0, 255, 60), mask=title_m)
            for sm in stk_masks: ov.paste((0, 255, 255, 60), mask=sm)
            fr = Image.alpha_composite(fr.convert('RGBA'), ov).convert('RGB')
            ImageDraw.Draw(fr).rectangle(SAFE, outline=(255, 0, 0), width=2)
            tiles.append(fr.resize((W * 2 // 5, H * 2 // 5), Image.LANCZOS))
    print('intro')
    an = card_annot(*INTRO_CARD_SPEC[:4], aspect=INTRO_CARD_SPEC[4], zoom=INTRO_CARD_SPEC[5], cap_size=INTRO_CARD_SPEC[6])
    cvis = place(INTRO_CARD, 540, INTRO_CARD_Y, thr=150); chk('p11 card', mbbox(cvis)); print(f'        face {an["face_px"][0]:.0f} px')
    cgirl = place(an['girl'], 540, INTRO_CARD_Y); ccap = place(an['cap'], 540, INTRO_CARD_Y)
    nm_ = place(INTRO_NAME, 540, 686, thr=100); chk('name', mbbox(nm_))
    if inter(nm_, cvis): fail('name overlaps the intro card')
    for spr, cx, cy, ang in INTRO_STK:
        sm = place(spr, cx, cy, scale=1.15, thr=100, rot=ang); chk('sticker', mbbox(sm))
        if not inter(sm, cvis): print('        (sticker is free-floating)')
        if inter(sm, cgirl) or inter(sm, ccap): fail('intro sticker covers her face / the caption')
    print('finale')
    an = card_annot(*FIN_CARD_SPEC[:4], aspect=FIN_CARD_SPEC[4], zoom=FIN_CARD_SPEC[5], cap_size=FIN_CARD_SPEC[6])
    cvis = place(FIN_CARD, 540, FIN_CARD_Y, scale=1.03, thr=150); chk('p19 card', mbbox(cvis)); print(f'        face {an["face_px"][0]:.0f} px')
    for name, lay, cy in (('T1', FIN_T1, 352), ('T2', FIN_T2, 500), ('T3', FIN_T3, 1532)):
        m = place(lay, 540, cy, thr=100); chk(name, mbbox(m))
        if inter(m, cvis): fail(f'{name} overlaps the finale card')
    if save_sheet and tiles:
        sheet = Image.new('RGB', (tiles[0].width * 3, tiles[0].height * 2), (30, 30, 30))
        for q, tile in enumerate(tiles): sheet.paste(tile, ((q % 3) * tile.width, (q // 3) * tile.height))
        p = os.path.join(OUT_DIR, KEY + '_check_pages.jpg'); sheet.save(p, quality=85); print('wrote', p)
    print('layout check', 'OK' if ok else 'HAS ISSUES')
    return ok

if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    print('duration %.2f s' % tl.duration)
    if '--check' in sys.argv:
        layout_check(); sys.exit(0)
    if '--preview' in sys.argv:
        for tt in (0.6, 2.5, 5.5, 9.0, 12.5, 16.0, 19.5, 23.0, 26.0, 28.5):
            t0 = time.time(); tl.frame(tt); print('frame %.1f: %.3fs' % (tt, time.time() - t0))
        preview(tl, os.path.join(OUT_DIR, KEY + '_prev16.jpg'), n=16, cols=4, scale=0.3)
        st = tl.starts()
        preview(tl, os.path.join(OUT_DIR, KEY + '_prev_pages.jpg'), n=12, cols=4, scale=0.3,
                times=[0.4, 0.9, 1.3, 2.4] + [st[k + 1] + PAGES[k]['dur'] * 0.55 + 0.28 for k in range(6)] + [10.75, 10.95])
        preview(tl, os.path.join(OUT_DIR, KEY + '_prev_trans.jpg'), n=12, cols=4, scale=0.3,
                times=[4.0, 4.25, 7.0, 7.3, 10.7, 11.0, 13.8, 14.1, 17.6, 17.9, 20.6, 20.9])
        preview(tl, os.path.join(OUT_DIR, KEY + '_prev_end.jpg'), n=12, cols=4, scale=0.3,
                times=[23.9, 24.1, 24.25, 24.4, 24.55, 24.8, 25.2, 25.8, 26.6, 28.0, 29.1, 29.4])
        sys.exit(0)
    out = os.path.join(OUT_DIR, KEY + '.mp4')
    t0 = time.time()
    encode_with_audio(tl, out, AUDIO, *AUDIO_FADE)
    print('encode time %.1f s' % (time.time() - t0))
    video_frames_sheet(out, os.path.join(OUT_DIR, KEY + '_sheet.jpg'), n=16, cols=4, scale=0.3)
    video_frames_sheet(out, os.path.join(OUT_DIR, KEY + '_sheet_big.jpg'), n=8, cols=4, scale=0.5)
