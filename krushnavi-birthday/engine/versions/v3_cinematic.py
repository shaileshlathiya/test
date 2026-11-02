"""
v3_cinematic.py - "Cinematic Family Story" birthday status video for Krushnavi (9:16, ~58 s, all 19 photos).
Round-2 fixer revision.

STORYBOARD (xfade semantics: a slide's transition overlaps the END of the previous slide)
  #  start   photo(s)            dur   trans-in       content / motion
  1   0.0    p11 hero            6.8   -              dim->light (frame 0 = soft, readable portrait, <=5 px blur) -> sharp by 1.6 s,
                                                      slow zoom-out 1.08->1.02; lower-third title stack over a warm scrim:
                                                      "Happy Birthday" (Playfair Italic), "Krushnavi" (Great Vibes, gold),
                                                      gold rule, "OUR LITTLE PRINCESS" (tracked)
  2   6.1    p07                 4.3   black 0.7      KB 1.00->1.12, chapter card "CHAPTER ONE / Our Sunshine" (fades out before the next move)
  3   9.8    p17 | p18 | p15     4.6   softblur 0.6   TRIPTYCH: tall centre tile + two side tiles land left->right under the blur (all in by 1.1 s)
  4  13.8    p12                 4.3   black 0.7      KB, chapter "CHAPTER TWO / Little Explorer"
  5  17.4    p13                 3.2   fade 0.6       KB 1.12->1.02 (cheeky smile)
  6  20.0    p02                 3.4   softblur 0.6   full-frame KB push-in 1.00->1.28 toward her under the elephant
  7  22.8    p08 / p01           4.0   softblur 0.6   big stacked landscape tiles (mirror reflection + ball pit), both in by 1.0 s
  8  26.2    p04                 4.3   black 0.7      KB (focus all), chapter "CHAPTER THREE / Mumma's Love"
  9  29.8    p05 + p16           4.0   softblur 0.6   ASYMMETRIC collage: wide top tile + 720x540 bottom-right tile keyed to her, heart + rule beside it
 10  33.2    p19                 3.4   softblur 0.6   KB 1.00->1.12 (cheek-to-cheek hug)
 11  36.0    p10                 4.3   black 0.7      KB, chapter "CHAPTER FOUR / Daddy's Girl"
 12  39.6    p06 | p14           4.0   softblur 0.6   STAGGERED duo: tall tiles offset vertically, short rules
 13  43.0    p03                 4.3   softblur 0.6   KB 1.05->1.10 (family raised above the scrim), chapter "CHAPTER FIVE / Family & Festivals"
 14  46.7    p09                 3.5   softblur 0.6   KB 1.10->1.00 (Ganesh idol)
 15  49.6    p11 finale          6.2   black 1.0      warm dark background, gold bokeh + sparkles BEHIND a gold-edged photo card,
                                                      "Happy Birthday", "Krushnavi", gold rule, "With all our love, Mumma & Papa"
 16  54.6    end card            3.2   black 0.8      dip to black, then "Krushnavi" (55.05 s), pulsing gold heart (55.3 s), "Many many happy returns / of the day"
                                                      (arrives with the 55.5 s closing chord); content stays on the final frame
 total 57.8 s

Palette: deep warm brown (#1a110d), cream (#f7efe2), soft gold (#d9b26a / #f1d99a).  Film look: photo grade (1.0, 1.06, 1.08),
8% warm wash on photo slides, low-alpha light leaks, soft vignette 0.32 (no grain: too costly to encode).
Fonts: Playfair Display Bold (chapter titles) / Playfair Display Italic (Happy Birthday, closing lines), Great Vibes (her name),
Montserrat Medium 34 px tracked caps (labels), Cormorant Garamond 62 (closing caption).
"""
import sys, os, math, time
SCRATCH = os.environ.get('BDAY_DIR') or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # folder holding bday_engine.py, assets/, fonts/
sys.path.insert(0, SCRATCH)
from bday_engine import *
import bday_engine as E

KEY = 'v3_cinematic'
OUT_DIR = os.path.join(ROOT, 'out')
os.makedirs(OUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------------- palette / grade
CREAM = hexc('#f7efe2')
GOLD = hexc('#d9b26a')
GOLD_L = hexc('#f1d99a')
GOLD_D = hexc('#a77f3a')
BROWN = (26, 17, 13, 255)
GOLD_GRAD = [hexc('#e9cf93'), hexc('#e2bd72'), hexc('#b98a3b'), hexc('#f4dfa3')]   # top stop darkened for contrast on white
GRADE = (1.0, 1.06, 1.08)            # mild warm film grade (6 % contrast / 8 % saturation, global only)
WARM = Image.new('RGBA', (W, H), (255, 196, 140, 20))   # ~8 % warm wash, photo slides only

# p11 (hero) is a soft capture: mild global unsharp mask before grading (no retouching, applied to the whole frame).
def _hero():
    im = photo(11).filter(ImageFilter.UnsharpMask(radius=1.6, percent=38, threshold=3))
    b, c, s = GRADE
    im = ImageEnhance.Contrast(im).enhance(c); im = ImageEnhance.Color(im).enhance(s)
    return im
E._IMG[('p11', GRADE)] = _hero()

# ----------------------------------------------------------------------------- fonts
F_TITLE = font('PlayfairDisplay[wght].ttf', 94, 'Bold')
F_HB = font('PlayfairDisplay-Italic[wght].ttf', 86, 'Italic')
F_HB_FIN = font('PlayfairDisplay-Italic[wght].ttf', 78, 'Italic')
F_END = font('PlayfairDisplay-Italic[wght].ttf', 56, 'Italic')
F_NAME = font('GreatVibes-Regular.ttf', 200)
F_NAME_FIN = font('GreatVibes-Regular.ttf', 170)
F_NAME_END = font('GreatVibes-Regular.ttf', 132)
F_TRACK = font('Montserrat[wght].ttf', 34, 'Medium')
F_CAP = font('CormorantGaramond[wght].ttf', 62, 'Medium')

# ----------------------------------------------------------------------------- transitions (local additions)
def tr_softblur(a, b, p):
    """gentler blur-dissolve than the engine's (peak 14 px instead of 36 px); the incoming frame settles from a
    2 % over-scale so the dissolve reads as an optical rack rather than a 'buffering' smear."""
    e = ease_in_out(p); r = 14 * math.sin(math.pi * e)
    if e < 0.999: b = E._scale_center(b, 1 + 0.02 * (1 - e))
    x = Image.blend(a, b, e)
    return x.filter(ImageFilter.GaussianBlur(r)) if r > 1 else x
TRANSITIONS['softblur'] = tr_softblur

# ----------------------------------------------------------------------------- static helpers
_CACHE = {}
def cached(k, fn):
    if k not in _CACHE: _CACHE[k] = fn()
    return _CACHE[k]

INK_W = {}
def tracked(text, fnt, tracking=10, fill=GOLD, shadow_on=True):
    """Letter-spaced small-caps style label rendered to a tight RGBA layer (PIL has no tracking)."""
    widths = [fnt.getlength(c) for c in text]
    tw = int(sum(widths) + tracking * (len(text) - 1))
    INK_W[text] = tw
    asc, desc = fnt.getmetrics(); th = asc + desc
    pad = 20
    layer = Image.new('RGBA', (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer); x = pad
    for c, w in zip(text, widths):
        d.text((x, pad), c, font=fnt, fill=fill); x += w + tracking
    if shadow_on: layer = shadow(layer, offset=(0, 3), blur=6, opacity=0.55)
    return layer

def rule_layer(w, color=GOLD, thick=2, diamond=9):
    """thin horizontal rule with a small diamond in the middle."""
    h = max(diamond * 2 + 6, thick + 6)
    l = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(l); cy = h // 2
    d.line((0, cy, w, cy), fill=color, width=thick)
    if diamond:
        d.polygon([(w / 2, cy - diamond), (w / 2 + diamond, cy), (w / 2, cy + diamond), (w / 2 - diamond, cy)], fill=color)
    return l

def draw_rule(fr, cx, cy, half, color=GOLD, alpha=1.0, thick=2, diamond=9):
    """animated rule growing from its centre: half = current half-length in px."""
    if half < 2 or alpha <= 0.01: return
    w = int(half * 2) + 2; h = diamond * 2 + 6
    l = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(l); y = h // 2
    d.line((0, y, w, y), fill=color, width=thick)
    if diamond:
        d.polygon([(w / 2, y - diamond), (w / 2 + diamond, y), (w / 2, y + diamond), (w / 2 - diamond, y)], fill=color)
    blit(fr, l, cx, cy, alpha=alpha)

def scrim(y_from, y_to, color=(18, 11, 8), a_max=175):
    """bottom scrim: transparent at y_from -> color at y_to and below."""
    return cached(('scrim', y_from, y_to, color, a_max), lambda: vgradient(W, H, [color + (0,), color + (a_max,)], y0=y_from, y1=y_to))

def warm_bg():
    return cached('warm_bg', lambda: vgradient(W, H, [hexc('#2b1b13'), hexc('#1a110d'), hexc('#120b08')]))

def soft_shadow_rect(w, h, radius, blur=26, opacity=0.6, offset=(0, 20)):
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(base).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=(0, 0, 0, 255))
    return shadow(base, offset=offset, blur=blur, opacity=opacity)

def shadow_for(w, h, r=12, **kw):
    return cached(('shadow', w, h, r, tuple(sorted(kw.items()))), lambda: soft_shadow_rect(w, h, r, **kw))

# ----------------------------------------------------------------------------- global overlays
LEAK = LightLeak(colors=[hexc('#ffb36b'), hexc('#ffd27a'), hexc('#ff9a8b')], n=3, seed=5, size=900, alpha=0.13, speed=0.07)
VIG = vignette(0.32, power=2.2)

def overlay(fr, t):
    # NOTE: no per-frame film grain - random noise makes x264 at crf 19 balloon to ~30 Mbps (200 MB file).
    LEAK.draw(fr, t)
    fr.alpha_composite(VIG)

# ----------------------------------------------------------------------------- text layers (built once)
def T(key_, fn): return cached(('text', key_), fn)
def t_hb(): return T('hb', lambda: text_layer('Happy Birthday', F_HB, fill=CREAM, shadow_c=(0, 0, 0, 200), shadow_off=(0, 6), shadow_blur=11))
def t_hb_fin(): return T('hb_fin', lambda: text_layer('Happy Birthday', F_HB_FIN, fill=CREAM, shadow_c=(0, 0, 0, 120), shadow_off=(0, 5), shadow_blur=10))
def t_name(): return T('name', lambda: text_layer('Krushnavi', F_NAME, gradient=GOLD_GRAD, shadow_c=(0, 0, 0, 190), shadow_off=(0, 8), shadow_blur=14))
def t_name_fin(): return T('name_fin', lambda: text_layer('Krushnavi', F_NAME_FIN, gradient=GOLD_GRAD, shadow_c=(0, 0, 0, 150), shadow_off=(0, 6), shadow_blur=12))
def t_name_end(): return T('name_end', lambda: text_layer('Krushnavi', F_NAME_END, gradient=GOLD_GRAD, shadow_c=(0, 0, 0, 120), shadow_off=(0, 4), shadow_blur=10))
def t_sub(): return T('sub', lambda: tracked('OUR LITTLE PRINCESS', F_TRACK, 10, GOLD_L))
def t_love(): return T('love', lambda: text_layer('With all our love, Mumma & Papa', F_CAP, fill=CREAM, shadow_c=(0, 0, 0, 130), shadow_off=(0, 4), shadow_blur=8))
def t_many(): return T('many', lambda: text_layer('Many many happy returns\nof the day', F_END, fill=GOLD_L, spacing=16,
                                                    shadow_c=(0, 0, 0, 120), shadow_off=(0, 4), shadow_blur=8))

CHAPTERS = {
    'sun': ('CHAPTER ONE', 'Our Sunshine'),
    'exp': ('CHAPTER TWO', 'Little Explorer'),
    'mum': ('CHAPTER THREE', "Mumma's Love"),
    'dad': ('CHAPTER FOUR', "Daddy's Girl"),
    'fam': ('CHAPTER FIVE', 'Family & Festivals'),
}
def chapter_layers(ch):
    label, title = CHAPTERS[ch]
    lab = T(('lab', ch), lambda: tracked(label, F_TRACK, 10, GOLD_L))
    tit = T(('tit', ch), lambda: text_layer(title, F_TITLE, fill=CREAM, shadow_c=(0, 0, 0, 160), shadow_off=(0, 6), shadow_blur=12))
    return lab, tit

LABEL_Y, TITLE_Y = 1352, 1452
def chapter_overlay(fr, t, ch, dur, t0=0.5, label_y=LABEL_Y, title_y=TITLE_Y):
    """chapter card: tracked label with growing flanking lines, then the title rising in.
    Everything fades out before the slide's outgoing transition starts (no ghosting over the next photo)."""
    lab, tit = chapter_layers(ch)
    out = 1 - ease_in_out_sine(seg(t, dur - 1.0, dur - 0.6))     # ~0.6 s more readable title; 0 before any softblur starts, <15 % when a black dip begins
    g1 = ease_out_cubic(seg(t, t0, t0 + 0.7)); u1 = g1 * out
    u2 = ease_out_cubic(seg(t, t0 + 0.2, t0 + 1.05))
    if u1 > 0.01:
        blit(fr, lab, W / 2, label_y, alpha=u1)
        half_w = INK_W[CHAPTERS[ch][0]] / 2 + 26          # true ink half width + gap
        ln = 110 * g1
        for sgn in (-1, 1):
            cx = W / 2 + sgn * (half_w + ln / 2)
            l = Image.new('RGBA', (int(ln) + 2, 6), (0, 0, 0, 0))
            ImageDraw.Draw(l).line((0, 3, int(ln) + 2, 3), fill=GOLD, width=2)
            blit(fr, l, cx, label_y, alpha=u1 * 0.9)
    if u2 > 0.01 and out > 0.01:
        blit(fr, tit, W / 2, title_y + (1 - u2) * 28, alpha=u2 * out)

# ----------------------------------------------------------------------------- slide builders
def full_slide(i, dur, z0=1.0, z1=1.12, p0=(0, 0), p1=(0, 0), focus='girl', chapter=None, y_bias=0.0,
               scrim_from=960, scrim_to=1760, label_y=LABEL_Y, title_y=TITLE_Y, t0=0.5):
    sc = scrim(scrim_from, scrim_to, a_max=205)
    def render(t):
        im = kenburns(i, W, H, t / dur, z0, z1, p0, p1, focus=focus, grade=GRADE, y_bias=y_bias)
        fr = rgba(im)
        fr.alpha_composite(WARM)
        if chapter:
            fr.alpha_composite(sc)
            chapter_overlay(fr, t, chapter, dur, t0=t0, label_y=label_y, title_y=title_y)
        return fr
    return render

def opening(dur=6.8):
    sc = scrim(1000, 1700, a_max=215)
    def render(t):
        im = kenburns(11, W, H, t / dur, 1.08, 1.02, (0, 0.015), (0, 0), focus='girl', grade=GRADE)
        fr = rgba(im)
        bp = 1 - ease_out_cubic(seg(t, 0.0, 1.6))
        if bp > 0.03:
            fr = fr.filter(ImageFilter.GaussianBlur(0.8 + bp * 4.2))   # full-res, max 5 px at frame 0: her eyes/smile stay readable in the status thumbnail
        fr.alpha_composite(WARM)
        fr.alpha_composite(sc)
        dk = 1 - ease_out_cubic(seg(t, 0.0, 1.4))
        if dk > 0.005: tint(fr, (12, 7, 5, int(62 * dk)))        # frame 0 is softly dimmed (~24 %), never black
        # lower-third title stack (her face is in the upper half; nothing is ever drawn over her hair or face)
        u1 = ease_out_cubic(seg(t, 0.9, 1.9)); blit(fr, t_hb(), W / 2, 1222 + (1 - u1) * 26, alpha=u1)
        u2 = ease_out_cubic(seg(t, 1.8, 2.8)); blit(fr, t_name(), W / 2, 1400, scale=lerp(0.96, 1.0, u2), alpha=u2)
        u3 = ease_in_out_sine(seg(t, 2.6, 3.6)); draw_rule(fr, W / 2, 1518, 290 * u3, alpha=u3)
        u4 = ease_out_cubic(seg(t, 3.3, 4.2)); blit(fr, t_sub(), W / 2, 1578 + (1 - u4) * 16, alpha=u4)
        return fr
    return render

BOKEH_DUO = Particles('bokeh', n=18, seed=21, colors=[hexc('#e8c27a'), hexc('#f5dfae'), hexc('#c99a4c')], size=(70, 190), speed=(30, 70), alpha=0.42, sway=30)

def tile(i, tw, th, zoom, focus='girl', keep='auto', radius=12, y_bias=0.0):
    im = fit(i, tw, th, zoom=zoom, focus=focus, keep=keep, grade=GRADE, y_bias=y_bias)
    im = apply_mask(im, rounded_mask(tw, th, radius))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, tw - 1, th - 1), radius=radius, outline=(241, 217, 154, 150), width=2)
    return im

def collage_bg(i):
    """blurred photo glowing warm through the free bands (target luma ~70-90, not a black void)."""
    return blur_bg(i, dark=0.58, blur=42, sat=0.95, tint=(55, 32, 16, 52))

def place(fr, i, x, y, w, h, u, dx, dy, z, focus='girl', keep='auto', shadow_kw=None, y_bias=0.0):
    """tile at top-left (x, y) sliding in from offset (dx, dy) with progress u (eased already)."""
    if u <= 0.01: return
    cx = x + w / 2 + dx * (1 - u); cy = y + h / 2 + dy * (1 - u)
    blit(fr, shadow_for(w, h, 12, **(shadow_kw or {})), cx, cy, alpha=u)
    blit(fr, tile(i, w, h, z, focus, keep, y_bias=y_bias), cx, cy, alpha=u)

def triptych(a, b, c, dur, bg_of=None):
    """three tiles: a (left, 286x1000) | b (centre, 340x1200, in front) | c (right, 286x1000); tiles land left->right under the softblur."""
    SW, SH, MW, MH, gap = 286, 1000, 340, 1200, 14
    xa = 70; xb = xa + SW + gap; xc = xb + MW + gap             # right edge = 1010
    ya, yb = 430, 330
    bg = collage_bg(bg_of or b)
    orn = cached(('orn', 420), lambda: rule_layer(420))
    def render(t):
        fr = new_frame(BROWN); fr.alpha_composite(bg)
        BOKEH_DUO.draw(fr, t)
        z = lerp(1.0, 1.08, ease_in_out_sine(t / dur))
        ua = ease_out_cubic(seg(t, 0.10, 0.80)); ub = ease_out_cubic(seg(t, 0.25, 0.95)); uc = ease_out_cubic(seg(t, 0.40, 1.10))
        place(fr, a, xa, ya, SW, SH, ua, -50, 0, z)
        place(fr, c, xc, ya, SW, SH, uc, 50, 0, z)
        place(fr, b, xb, yb, MW, MH, ub, 0, 50, z)
        uo = ease_out_cubic(seg(t, 1.0, 1.7))
        blit(fr, orn, W / 2, 1570, scale=max(0.05, uo), alpha=uo)
        return fr
    return render

def stack_big(a, b, dur, fa='girl', fb='girl', ka='auto', kb='auto', bg_of=None):
    """two big landscape tiles 940x600 (y 330 / 944) sliding in from top / bottom under the softblur."""
    TW, TH, gap = 940, 600, 14
    x0, ya, yb = 70, 330, 330 + TH + gap
    bg = collage_bg(bg_of or b)
    orn = cached(('orn', 420), lambda: rule_layer(420))
    def render(t):
        fr = new_frame(BROWN); fr.alpha_composite(bg)
        BOKEH_DUO.draw(fr, t)
        z = lerp(1.0, 1.08, ease_in_out_sine(t / dur))
        ua = ease_out_cubic(seg(t, 0.10, 0.80)); ub = ease_out_cubic(seg(t, 0.30, 1.00))
        place(fr, a, x0, ya, TW, TH, ua, 0, -50, z * 1.08, fa, ka)
        place(fr, b, x0, yb, TW, TH, ub, 0, 50, z * 1.04, fb, kb)
        uo = ease_out_cubic(seg(t, 1.0, 1.7))
        blit(fr, orn, W / 2, 1572, scale=max(0.05, uo), alpha=uo)
        return fr
    return render

def asym(a, b, dur, bg_of=None):
    """asymmetric collage: wide top tile a (940x700) + bottom-right tile b (720x540, zoomed toward her); gold heart + short rule beside it."""
    AW, AH, BW, BH = 940, 700, 720, 540
    xa, ya = 70, 330
    xb, yb = 1010 - BW, ya + AH + 14            # 290, 1044  -> bottom 1584
    bg = collage_bg(bg_of or a)
    heart = cached('heart_s', lambda: heart_sprite(40, GOLD_L))
    rule = cached(('orn', 180), lambda: rule_layer(180, diamond=7))
    lx = (70 + xb - 14) / 2                      # 173: centre of the free left column (x 70-276)
    def render(t):
        fr = new_frame(BROWN); fr.alpha_composite(bg)
        BOKEH_DUO.draw(fr, t)
        z = lerp(1.0, 1.07, ease_in_out_sine(t / dur))
        ua = ease_out_cubic(seg(t, 0.10, 0.80)); ub = ease_out_cubic(seg(t, 0.30, 1.00))
        place(fr, a, xa, ya, AW, AH, ua, 0, -50, z * 1.15, 'all', 'all')
        place(fr, b, xb, yb, BW, BH, ub, 50, 0, z * 1.16, 'girl', 'all', y_bias=0.10)   # her face ~185 px; keep='all' holds mum, y_bias keeps the hands
        uo = ease_out_cubic(seg(t, 1.0, 1.7))
        if uo > 0.01:
            ps = 1 + 0.05 * math.sin(t * 2 * math.pi / 1.6)
            blit(fr, heart, lx, 1246, scale=ps * uo, alpha=uo)
            blit(fr, rule, lx, 1318, scale=max(0.05, uo), alpha=uo)
        return fr
    return render

def duo_stagger(a, b, dur, bg_of=None):
    """two tall tiles 463x1140, vertically staggered (left high, right low), short rules in the free corners."""
    TW, TH, gap = 463, 1140, 14
    xa, xb = 70, 70 + TW + gap
    ya, yb = 300, 440
    bg = collage_bg(bg_of or b)
    rule = cached(('orn', 300), lambda: rule_layer(300, diamond=7))
    def render(t):
        fr = new_frame(BROWN); fr.alpha_composite(bg)
        BOKEH_DUO.draw(fr, t)
        z = lerp(1.0, 1.06, ease_in_out_sine(t / dur))
        ua = ease_out_cubic(seg(t, 0.10, 0.80)); ub = ease_out_cubic(seg(t, 0.30, 1.00))
        place(fr, a, xa, ya, TW, TH, ua, -50, 0, z * 1.12, 'all', 'all')      # p06 zoomed a touch: her face ~125 px, dad kept by keep='all'
        place(fr, b, xb, yb, TW, TH, ub, 50, 0, z, 'all', 'all')
        uo = ease_out_cubic(seg(t, 1.0, 1.7))
        blit(fr, rule, xa + TW / 2, ya + TH + 62, scale=max(0.05, uo), alpha=uo)       # under the left tile  (y 1502)
        blit(fr, rule, xb + TW / 2, yb - 60, scale=max(0.05, uo), alpha=uo)            # above the right tile (y 380)
        return fr
    return render

BOKEH_FIN = Particles('bokeh', n=12, seed=31, colors=[hexc('#e8c27a'), hexc('#f5dfae'), hexc('#c99a4c')], size=(60, 200), speed=(30, 70), alpha=0.32, sway=30)
SPARK_FIN = Particles('sparkle', n=34, seed=41, colors=[hexc('#ffe9b0'), hexc('#f1d99a')], size=(9, 24), speed=(40, 90), alpha=0.95, twinkle=1.0)
BOKEH_END = Particles('bokeh', n=10, seed=51, colors=[hexc('#e8c27a'), hexc('#f5dfae')], size=(60, 170), speed=(30, 60), alpha=0.22, sway=30)

def finale(dur=6.2):
    CW, CH, R = 640, 800, 18
    cy_card = 858
    sh = shadow_for(CW, CH, R, blur=30, opacity=0.8, offset=(0, 24))
    def render(t):
        fr = new_frame(BROWN); fr.alpha_composite(warm_bg())
        BOKEH_FIN.draw(fr, t); SPARK_FIN.draw(fr, t)
        uc = ease_out_cubic(seg(t, 0.4, 1.4))
        if uc > 0.01:
            z = lerp(1.02, 1.10, ease_in_out_sine(t / dur))
            im = fit(11, CW, CH, zoom=z, focus='girl', grade=GRADE)
            im = apply_mask(im, rounded_mask(CW, CH, R))
            ImageDraw.Draw(im).rounded_rectangle((0, 0, CW - 1, CH - 1), radius=R, outline=GOLD_L, width=4)
            s = lerp(0.94, 1.0, uc)
            blit(fr, sh, W / 2, cy_card, scale=s, alpha=uc)
            blit(fr, im, W / 2, cy_card, scale=s, alpha=uc)
        u1 = ease_out_cubic(seg(t, 1.0, 1.9)); blit(fr, t_hb_fin(), W / 2, 356 + (1 - u1) * 26, alpha=u1)
        u2 = ease_out_cubic(seg(t, 1.6, 2.6)); blit(fr, t_name_fin(), W / 2, 1368, scale=lerp(0.96, 1.0, u2), alpha=u2)
        u3 = ease_in_out_sine(seg(t, 2.3, 3.2)); draw_rule(fr, W / 2, 1470, 230 * u3, alpha=u3, diamond=8)
        u4 = ease_out_cubic(seg(t, 2.8, 3.7)); blit(fr, t_love(), W / 2, 1546 + (1 - u4) * 16, alpha=u4)
        return fr
    return render

def end_card(dur=3.6):
    heart = cached('heart', lambda: heart_sprite(62, GOLD_L))
    glow = cached('heart_glow', lambda: radial_sprite(280, with_alpha(hexc('#e8c27a'), 110), power=2.0))
    def render(t):
        fr = new_frame(BROWN); fr.alpha_composite(warm_bg())
        BOKEH_END.draw(fr, t + 3.0)
        # the card is reached through a 0.8 s dip to black (nothing can overlap her face), so the content can start right away
        un = ease_out_cubic(seg(t, 0.45, 1.10)); blit(fr, t_name_end(), W / 2, 790, scale=lerp(0.96, 1.0, un), alpha=un)
        uh = ease_out_cubic(seg(t, 0.70, 1.30))
        if uh > 0.01:
            ps = 1 + 0.06 * math.sin((t - 1.3) * 2 * math.pi / 1.6)
            blit(fr, glow, W / 2, 972, scale=ps * 1.05, alpha=0.9 * uh)
            blit(fr, heart, W / 2, 972, scale=ps * lerp(0.75, 1.0, uh), alpha=uh)
        u2 = ease_out_cubic(seg(t, 0.95, 1.65)); blit(fr, t_many(), W / 2, 1176 + (1 - u2) * 14, alpha=u2)
        return fr        # content stays fully visible on the final frame
    return render

# ----------------------------------------------------------------------------- timeline
def build():
    tl = Timeline()
    tl.add(6.8, opening(6.8), name='opening p11')
    tl.add(4.3, full_slide(7, 4.3, 1.0, 1.12, chapter='sun'), trans='black', tdur=0.7, name='ch1 p07')
    tl.add(4.6, triptych(17, 18, 15, 4.6, bg_of=18), trans='softblur', tdur=0.6, name='trip p17|p18|p15')
    tl.add(4.3, full_slide(12, 4.3, 1.0, 1.12, chapter='exp'), trans='black', tdur=0.7, name='ch2 p12')
    tl.add(3.2, full_slide(13, 3.2, 1.12, 1.02), trans='fade', tdur=0.6, name='p13')
    tl.add(3.4, full_slide(2, 3.4, 1.0, 1.28, (-0.15, 0), (0, 0)), trans='softblur', tdur=0.6, name='p02')
    tl.add(4.0, stack_big(8, 1, 4.0, fa='all', fb='girl', ka='all', kb='girl', bg_of=1), trans='softblur', tdur=0.6, name='stack p08/p01')
    tl.add(4.3, full_slide(4, 4.3, 1.0, 1.12, focus='all', chapter='mum', scrim_from=1180, scrim_to=1650,
                           label_y=1376, title_y=1476), trans='black', tdur=0.7, name='ch3 p04')
    tl.add(4.0, asym(5, 16, 4.0, bg_of=16), trans='softblur', tdur=0.6, name='asym p05+p16')
    tl.add(3.4, full_slide(19, 3.4, 1.0, 1.12, focus='all'), trans='softblur', tdur=0.6, name='p19')
    tl.add(4.3, full_slide(10, 4.3, 1.0, 1.12, focus='all', chapter='dad'), trans='black', tdur=0.7, name='ch4 p10')
    tl.add(4.0, duo_stagger(6, 14, 4.0, bg_of=14), trans='softblur', tdur=0.6, name='duo p06|p14')
    tl.add(4.3, full_slide(3, 4.3, 1.05, 1.10, focus='all', chapter='fam', y_bias=0.11,
                           scrim_from=1170, scrim_to=1650, label_y=1400, title_y=1500, t0=0.8), trans='softblur', tdur=0.6, name='ch5 p03')
    tl.add(3.5, full_slide(9, 3.5, 1.10, 1.0, focus='all'), trans='softblur', tdur=0.6, name='p09')
    tl.add(6.2, finale(6.2), trans='black', tdur=1.0, name='finale p11')
    tl.add(3.2, end_card(3.2), trans='black', tdur=0.8, name='end card')     # 3.2 s keeps the total at 57.8 s
    tl.overlays.append(overlay)
    return tl

PHOTOS_USED = ['p11', 'p07', 'p17', 'p18', 'p15', 'p12', 'p13', 'p02', 'p08', 'p01', 'p04', 'p05', 'p16', 'p19', 'p10', 'p06', 'p14', 'p03', 'p09']
AUDIO = os.path.join(AUDIO_DIR, 'hb_v3_593.wav')      # music.make_track(59.3, bpm=110): 4th verse ends 55.3 s, closing chord 55.9 s rings under the fade; encode() trims to 57.8 s

def ensure_audio(tl):
    if not os.path.exists(AUDIO):
        import importlib.util
        spec = importlib.util.spec_from_file_location('music', os.path.join(SCRATCH, 'music.py'))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        m.make_track(59.3, AUDIO, bpm=110)
    return AUDIO

if __name__ == '__main__':
    tl = build()
    print('duration %.2f s' % tl.duration)
    for s, st in zip(tl.slides, tl.starts()): print('  %6.2f  %-18s dur %.1f  %s %.1f' % (st, s.name, s.dur, s.trans, s.tdur))
    if '--preview' in sys.argv:
        for nm, fn in (('hb', t_hb), ('name', t_name), ('sub', t_sub), ('love', t_love), ('many', t_many), ('name_end', t_name_end)):
            l = fn(); bb = l.getchannel('A').getbbox(); print('layer', nm, l.size, 'ink bbox', bb)
        preview(tl, os.path.join(OUT_DIR, KEY + '_prev16.jpg'), n=16, cols=4, scale=0.3)
        preview(tl, os.path.join(OUT_DIR, KEY + '_prev_open.jpg'), n=8, cols=4, scale=0.3, times=[0.0, 0.6, 1.5, 2.5, 3.5, 4.6, 6.0, 6.5])
        preview(tl, os.path.join(OUT_DIR, KEY + '_prev_mid.jpg'), n=12, cols=4, scale=0.3, times=[7.6, 10.1, 10.6, 12.5, 15.5, 18.6, 21.5, 23.3, 24.5, 28.0, 30.4, 32.5])
        preview(tl, os.path.join(OUT_DIR, KEY + '_prev_end.jpg'), n=12, cols=4, scale=0.3, times=[34.5, 37.8, 40.2, 42.0, 43.4, 45.5, 47.5, 51.5, 53.8, 55.1, 55.6, 57.7])
        snap(tl, 4.6, os.path.join(OUT_DIR, KEY + '_snap_open.jpg'), scale=0.5)
        snap(tl, 45.5, os.path.join(OUT_DIR, KEY + '_snap_ch5.jpg'), scale=0.5)
        snap(tl, 12.5, os.path.join(OUT_DIR, KEY + '_snap_trip.jpg'), scale=0.5)
        snap(tl, 32.5, os.path.join(OUT_DIR, KEY + '_snap_asym.jpg'), scale=0.5)
        snap(tl, 42.0, os.path.join(OUT_DIR, KEY + '_snap_duo.jpg'), scale=0.5)
        snap(tl, 25.5, os.path.join(OUT_DIR, KEY + '_snap_stack.jpg'), scale=0.5)
        snap(tl, 53.8, os.path.join(OUT_DIR, KEY + '_snap_finale.jpg'), scale=0.5)
        snap(tl, 57.7, os.path.join(OUT_DIR, KEY + '_snap_end.jpg'), scale=0.5)
        for tt in (3.0, 8.3, 12.5, 25.5, 32.5, 42.0, 53.8):
            t0 = time.time(); tl.frame(tt); print('frame %.1f: %.3f s' % (tt, time.time() - t0))
        sys.exit(0)
    out = os.path.join(OUT_DIR, KEY + '.mp4')
    audio = ensure_audio(tl)
    t0 = time.time()
    encode(tl, out, audio=audio, workers=3, preset='medium', crf=19, audio_fade=1.0)   # chord (55.5 s) rings; only the last 1 s fades
    print('encode time %.1f s' % (time.time() - t0))
    video_frames_sheet(out, os.path.join(OUT_DIR, KEY + '_sheet.jpg'), n=16, cols=4, scale=0.3)
    video_frames_sheet(out, os.path.join(OUT_DIR, KEY + '_sheet_big.jpg'), n=8, cols=4, scale=0.5)
