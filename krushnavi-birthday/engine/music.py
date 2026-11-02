"""Royalty-free synthesized 'Happy Birthday' music-box track generator (melody is public domain)."""
import numpy as np, wave, sys, math

SR = 44100

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

# Happy Birthday in G major, 3/4. (midi note, beats)
MEL = [(62,.75),(62,.25),(64,1),(62,1),(67,1),(66,2),
       (62,.75),(62,.25),(64,1),(62,1),(69,1),(67,2),
       (62,.75),(62,.25),(74,1),(71,1),(67,1),(66,1),(64,1),
       (72,.75),(72,.25),(71,1),(67,1),(69,1),(67,2)]
# chords per bar (after 1-beat pickup): root midi list
CHORDS = [[55,59,62],[57,62,66],[57,62,66],[55,59,62],[55,59,62],[55,60,64],[55,59,62],[55,59,62]]

def musicbox_note(f, dur, vel=1.0, bright=1.0):
    n = int(SR * dur); t = np.arange(n) / SR
    env = np.exp(-t * (2.2 + f / 900.0)) * (1 - np.exp(-t * 2500))
    s = (np.sin(2*np.pi*f*t) + 0.45*bright*np.sin(2*np.pi*2.0*f*t)*np.exp(-t*3)
         + 0.22*bright*np.sin(2*np.pi*3.01*f*t)*np.exp(-t*5) + 0.12*np.sin(2*np.pi*4.2*f*t)*np.exp(-t*8))
    return s * env * vel

def pad_note(f, dur, vel=0.12):
    n = int(SR * dur); t = np.arange(n) / SR
    a = np.minimum(1, t / 0.6); r = np.minimum(1, (dur - t) / 0.8)
    s = np.sin(2*np.pi*f*t) + 0.3*np.sin(2*np.pi*2*f*t) + 0.15*np.sin(2*np.pi*f*t*1.003)
    return s * a * r * vel

def add(buf, start, sig):
    i = int(start * SR); j = min(len(buf), i + len(sig))
    if j > i: buf[i:j] += sig[:j - i]

def render_song(buf, t0, bpm, transpose=0, harmony=False, pad=True, vel=1.0):
    beat = 60.0 / bpm; t = t0
    for (n, b) in MEL:
        add(buf, t, musicbox_note(midi(n + 12 + transpose), min(2.5, b*beat + 1.2), vel))
        if harmony:
            add(buf, t, musicbox_note(midi(n + 12 + transpose - 12), min(2.5, b*beat + 1.0), vel*0.45, 0.6))
        t += b * beat
    if pad:
        tb = t0 + 1 * beat  # bars start after pickup
        for ch in CHORDS:
            for k, n in enumerate(ch):
                add(buf, tb, pad_note(midi(n + transpose), 3*beat + 0.3, 0.09))
                add(buf, tb + k*0.5*beat, musicbox_note(midi(n + transpose), 1.2, 0.22, 0.5))
            tb += 3 * beat
    return t

def sparkle(buf, t0, dur=1.6, base=79):
    seq = [0,4,7,12,16,19,24,28]
    for k, s in enumerate(seq):
        add(buf, t0 + k*dur/len(seq), musicbox_note(midi(base + s), 1.6, 0.5))

def reverb(x, mix=0.22):
    n = int(SR * 0.9); rng = np.random.default_rng(7)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR*0.22)); ir[0] = 1; ir /= np.abs(ir).sum() / 6
    y = np.fft.irfft(np.fft.rfft(x, len(x)+n) * np.fft.rfft(ir, len(x)+n))[:len(x)]
    return x + mix * y

def make_track(duration, out, bpm=104, seed=0, style="musicbox"):
    buf = np.zeros(int(SR * (duration + 4)))
    beat = 60.0 / bpm; song_len = 24 * beat
    t = 0.0
    sparkle(buf, 0.0); t = 1.4
    k = 0
    while t + song_len * 0.6 < duration:
        render_song(buf, t, bpm, transpose=0 if k % 2 == 0 else 0, harmony=(k % 2 == 1), vel=1.0 if k % 2 == 0 else 0.9)
        t += song_len + (0.3 if k % 2 == 0 else 0.6)
        k += 1
    # ending chord + sparkle
    for n in [55, 59, 62, 67, 71, 74]:
        add(buf, min(t, duration - 2.5), musicbox_note(midi(n + 12), 3.0, 0.5))
    buf = reverb(buf)
    buf = buf[:int(SR * duration)]
    # fades
    fi = int(SR * 0.4); fo = int(SR * 2.5)
    buf[:fi] *= np.linspace(0, 1, fi); buf[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    buf /= (np.abs(buf).max() + 1e-9); buf *= 0.85
    # gentle stereo: right channel slightly delayed/attenuated for width
    d = int(SR * 0.012)
    L = buf; R = np.concatenate([np.zeros(d), buf[:-d]]) * 0.95
    st = np.stack([0.8*L + 0.2*R, 0.8*R + 0.2*L], 1)
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return out

if __name__ == '__main__':
    dur = float(sys.argv[1]); out = sys.argv[2]; bpm = float(sys.argv[3]) if len(sys.argv) > 3 else 104
    make_track(dur, out, bpm)
    print('wrote', out)
