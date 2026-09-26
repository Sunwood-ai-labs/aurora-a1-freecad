# Original procedural BGM for the making-of video (numpy only). 120 BPM, bar = 2 s,
# sections aligned to scene cuts. Run with a Python that has numpy (FreeCAD's works).
import sys
import wave
import numpy as np

SR = 44100
BPM = 120
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 53                      # 106 s
N = int(BARS * BAR * SR)
rng = np.random.default_rng(7)

# per-bar intensity: 0 pad, 1 +hats/pulse, 2 groove, 3 full(+arp), 4 breakdown, 5 outro
LEVEL = ([0] * 4 + [1] * 4 + [2] * 16 + [3] * 7 + [4] * 9 + [3] * 8 + [5] * 5)
assert len(LEVEL) == BARS
# i - VI - III - VII in A minor (root midi notes)
PROG = [(57, [0, 3, 7]), (53, [0, 4, 7]), (48, [0, 4, 7]), (55, [0, 4, 7])]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def t_arr(n):
    return np.arange(n) / SR


def lowpass(x, cutoff):
    k = 255
    n = np.arange(k) - (k - 1) / 2
    h = np.sinc(2 * cutoff / SR * n) * np.hanning(k)
    h /= h.sum()
    L = len(x) + k - 1
    F = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(h, F), F)[:L]
    return y[(k - 1) // 2:(k - 1) // 2 + len(x)]


def saw(f, n, detune=0.0):
    ph = (np.cumsum(np.full(n, f * (1 + detune) / SR)) + rng.random()) % 1.0
    return 2 * ph - 1


def env_adsr(n, a, d, s, r):
    e = np.full(n, s)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na, endpoint=False)
    nd2 = min(nd, max(0, n - na))
    e[na:na + nd2] = np.linspace(1, s, nd2, endpoint=False)
    if nr > 0:
        e[-min(nr, n):] *= np.linspace(1, 0, min(nr, n))
    return e


def add(buf, start_s, sig, gain=1.0):
    i = int(start_s * SR)
    j = min(N, i + len(sig))
    if i < N:
        buf[i:j] += gain * sig[:j - i]


def kick():
    n = int(0.45 * SR)
    t = t_arr(n)
    f = 45 + 95 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7.5) + 0.25 * np.sin(ph * 2) * np.exp(-t * 30)


def hat(open_=False):
    n = int((0.22 if open_ else 0.05) * SR)
    x = np.diff(rng.standard_normal(n + 1))
    return x * np.exp(-t_arr(n) * (14 if open_ else 70)) * 0.35


def clap():
    n = int(0.25 * SR)
    x = rng.standard_normal(n)
    t = t_arr(n)
    e = np.exp(-t * 25) + 0.6 * np.exp(-np.maximum(t - 0.012, 0) * 30) * (t > 0.012)
    return lowpass(x * e, 3500) * 0.5


def bass_note(m, dur):
    n = int(dur * SR)
    x = saw(hz(m), n) + 0.5 * np.sin(2 * np.pi * hz(m - 12) * t_arr(n))
    return lowpass(x, 700) * env_adsr(n, 0.005, 0.12, 0.55, 0.05)


def pad_chord(root, ivs, dur):
    n = int(dur * SR)
    x = np.zeros(n)
    for iv in ivs:
        for dt in (-0.004, 0.0, 0.005):
            x += saw(hz(root + 12 + iv), n, dt)
    x = lowpass(x / (3 * len(ivs)), 1400)
    return x * env_adsr(n, 0.6, 0.3, 0.8, 0.5)


def pluck(m, dur=0.22):
    n = int(dur * SR)
    t = t_arr(n)
    sq = np.sign(np.sin(2 * np.pi * hz(m) * t))
    return lowpass(sq, 2600) * np.exp(-t * 16) * 0.5


def riser(dur):
    n = int(dur * SR)
    t = t_arr(n)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    seg = n // 8
    for k in range(8):
        a, b = k * seg, n if k == 7 else (k + 1) * seg
        out[a:b] = lowpass(x[a:b], 400 + 900 * k)
    return out * (t / t[-1]) ** 2 * 0.6


def impact():
    n = int(2.5 * SR)
    t = t_arr(n)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.2)
    noise = lowpass(rng.standard_normal(n), 1800) * np.exp(-t * 5) * 0.5
    return boom + noise


def main(out_path):
    drums = np.zeros(N)
    bass = np.zeros(N)
    pads = np.zeros(N)
    arps = np.zeros(N)
    fx = np.zeros(N)
    K, C = kick(), clap()
    for b in range(BARS):
        lv = LEVEL[b]
        t0 = b * BAR
        root, ivs = PROG[b % 4]
        # pads everywhere (outro fades)
        pg = 0.55 if lv in (0, 5) else 0.38
        add(pads, t0, pad_chord(root, ivs, BAR + 0.4), pg)
        if lv in (1, 2, 3, 4):
            for s in range(8):
                add(drums, t0 + s * BEAT / 2 + BEAT / 2 * (s % 2 == 0), hat(), 0.7 if lv == 1 else 1.0)
        if lv in (2, 3):
            for q in range(4):
                add(drums, t0 + q * BEAT, K, 0.95)
            add(drums, t0 + BEAT, C, 0.7)
            add(drums, t0 + 3 * BEAT, C, 0.7)
            add(drums, t0 + 3.5 * BEAT, hat(True), 0.6)
        if lv in (1, 2, 3, 4):
            step = BEAT / 2 if lv != 4 else BEAT
            s = 0.0
            while s < BAR - 1e-6:
                m = root - 12 + (7 if (lv == 3 and int(s / step) % 4 == 3) else 0)
                add(bass, t0 + s, bass_note(m, step * 0.9), 0.55 if lv != 1 else 0.35)
                s += step
        if lv == 3:
            seq = [0, ivs[1], ivs[2], 12, ivs[2], ivs[1], 0, ivs[2]]
            for s in range(16):
                add(arps, t0 + s * BEAT / 4, pluck(root + 12 + seq[s % 8]), 0.35)
        if lv == 4 and b % 2 == 1:
            for s in (0, 3, 6):
                add(arps, t0 + s * BEAT / 2, pluck(root + 24 + ivs[s % 3], 0.4), 0.3)
    # risers into the big cuts, impacts on them
    for cut in (48.0, 80.0, 96.0):
        add(fx, cut - 4.0, riser(4.0), 0.8)
        add(fx, cut, impact(), 0.9)
    add(fx, 0.0, impact(), 0.45)

    mix = 0.9 * drums + 0.8 * bass + 0.7 * pads + 0.6 * arps + 0.6 * fx
    # stereo: pads/arps widened with short delays
    d1, d2 = int(0.011 * SR), int(0.017 * SR)
    wide = 0.7 * pads + 0.6 * arps
    L = mix + 0.25 * np.concatenate([np.zeros(d1), wide[:-d1]])
    R = mix + 0.25 * np.concatenate([np.zeros(d2), wide[:-d2]])
    fade_in = np.minimum(1, t_arr(N) / 1.5)
    fade_out = np.clip((106.0 - t_arr(N)) / 6.0, 0, 1)
    st = np.stack([L, R], 1) * (fade_in * fade_out)[:, None]
    st = np.tanh(st / np.max(np.abs(st)) * 1.6) / np.tanh(1.6) * 0.89
    pcm = (st * 32767).astype("<i2")
    with wave.open(out_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    main(sys.argv[1])
