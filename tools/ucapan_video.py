"""Ubah kartu ucapan (gambar 1080x1920) menjadi video pendek dengan musik sesuai hari besar.

Pemakaian: python3 -I tools/ucapan_video.py kartu.jpg keluaran.mp4 SUASANA [durasi_detik]
SUASANA:
  lembut    - piano & pad hangat (Hari Ibu, Kartini, Hari Guru, Hari Pendidikan)
  islami    - tangga nada hijaz + rebana lembut, tenang (Isra Mikraj, Ramadan, Idulfitri, Iduladha, Tahun Baru Islam, Maulid)
  natal     - lonceng & celesta, melodi "Malam Kudus" (Franz Gruber 1818, domain publik) (Natal)
  paskah    - pad paduan suara tenang + piano (Paskah, Kenaikan Yesus Kristus)
  imlek     - pentatonik, petik (guzheng-like) + gong (Tahun Baru Imlek)
  nyepi     - tenang, genta & gamelan pelog pelan (Nyepi)
  waisak    - genta/singing bowl + pad tenang (Waisak)
  nasional  - mars bersemangat: snare, brass-like, mayor (HUT RI, Sumpah Pemuda, Pahlawan, Pancasila, Hari Jadi Binjai)
  tahunbaru - ceria, ketukan ringan, synth pluck (Tahun Baru Masehi)
Semua musik disintesis dari nol (bebas hak cipta). Video: zoom perlahan + fade, 30fps, H.264/AAC.
"""
import sys, subprocess, wave, math
import numpy as np

SR = 44100

def env(n, a=0.01, r=0.3):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
    return e

def tone(f, dur, kind="piano", vol=0.2):
    n = int(dur * SR); t = np.arange(n) / SR
    if kind == "piano":
        x = sum((0.6 ** k) * np.sin(2 * np.pi * f * (k + 1) * t) for k in range(5)) * env(n, 0.005, dur * 0.45)
    elif kind == "pad":
        x = (np.sin(2*np.pi*f*t) + 0.5*np.sin(2*np.pi*f*1.003*t) + 0.3*np.sin(2*np.pi*f*2*t)) * np.minimum(1, t/0.6) * np.minimum(1, (dur - t)/0.6)
    elif kind == "bell":
        x = (np.sin(2*np.pi*f*t) + 0.6*np.sin(2*np.pi*f*2.76*t) + 0.4*np.sin(2*np.pi*f*5.4*t)) * env(n, 0.002, 1.2)
    elif kind == "celesta":
        x = (np.sin(2*np.pi*f*t) + 0.3*np.sin(2*np.pi*f*4*t)) * env(n, 0.002, 0.6)
    elif kind == "pluck":  # Karplus-Strong
        p = max(2, int(SR / f)); buf = np.random.uniform(-1, 1, p); x = np.zeros(n)
        for i in range(n):
            x[i] = buf[i % p]; buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    elif kind == "brass":
        x = sum((1 / (k + 1)) * np.sin(2*np.pi*f*(k+1)*t) for k in range(6)) * np.minimum(1, t/0.05) * np.exp(-t/ (dur*0.9))
    elif kind == "gong":
        x = (np.sin(2*np.pi*f*t) + 0.5*np.sin(2*np.pi*f*1.48*t) + 0.3*np.sin(2*np.pi*f*2.3*t)) * env(n, 0.01, 2.5) * (1 + 0.1*np.sin(2*np.pi*3*t))
    else:
        x = np.sin(2*np.pi*f*t) * env(n)
    return vol * x

def drum(kind, vol=0.3):
    n = int(0.35 * SR); t = np.arange(n) / SR
    if kind == "kick":
        return vol * np.sin(2*np.pi*(60 + 80*np.exp(-t*30))*t) * np.exp(-t*12)
    if kind == "snare":
        return vol * (np.random.randn(n) * 0.6 + 0.4*np.sin(2*np.pi*190*t)) * np.exp(-t*18)
    if kind == "rebana":  # tung / tak
        return vol * (0.7*np.sin(2*np.pi*(180 + 60*np.exp(-t*40))*t) + 0.25*np.random.randn(n)*np.exp(-t*60)) * np.exp(-t*14)
    if kind == "hat":
        return vol * 0.4 * np.random.randn(n) * np.exp(-t*60)
    return np.zeros(n)

def hz(midi): return 440 * 2 ** ((midi - 69) / 12)

def put(buf, x, at):
    s = int(at * SR); e = min(len(buf), s + len(x))
    if s < len(buf): buf[s:e] += x[:e - s]

CHORDS_MAJ = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]  # C Am F G

def compose(mood, dur):
    L = int(dur * SR); b = np.zeros(L); rng = np.random.default_rng(7)
    if mood == "lembut":
        bpm = 70; beat = 60 / bpm
        for i, ch in enumerate(CHORDS_MAJ * 4):
            t0 = i * 4 * beat
            if t0 >= dur: break
            for n in ch: put(b, tone(hz(n - 12), 4 * beat, "pad", 0.05), t0)
            for k, n in enumerate([ch[0], ch[1], ch[2], ch[1]] * 2):
                put(b, tone(hz(n + 12), beat * 1.5, "piano", 0.09), t0 + k * beat / 2)
    elif mood == "islami":  # hijaz di D: D Eb F# G A Bb C
        scale = [62, 63, 66, 67, 69, 70, 72, 74]; bpm = 76; beat = 60 / bpm
        put(b, tone(hz(50), dur, "pad", 0.05), 0); put(b, tone(hz(57), dur, "pad", 0.03), 0)
        mel = [0, 1, 2, 3, 4, 3, 2, 1, 2, 3, 2, 1, 0, 0]
        for i in range(int(dur / beat)):
            if i % 2 == 0: put(b, drum("rebana", 0.12), i * beat)
            if i % 4 == 3: put(b, drum("rebana", 0.07), i * beat + beat / 2)
            n = scale[mel[i % len(mel)]]
            put(b, tone(hz(n), beat * 1.1, "pluck", 0.12), i * beat)
    elif mood == "natal":  # Malam Kudus (domain publik), G mayor 6/8 sederhana
        mel = [(67,3),(69,1),(67,2),(64,6),(67,3),(69,1),(67,2),(64,6),(74,4),(74,2),(71,6),(72,4),(72,2),(67,6)]
        q = 0.32; t = 0.2
        put(b, tone(hz(43), dur, "pad", 0.05), 0); put(b, tone(hz(55), dur, "pad", 0.03), 0)
        for n, d in mel:
            if t >= dur: break
            put(b, tone(hz(n + 12), d * q * 1.2, "celesta", 0.14), t); put(b, tone(hz(n), d * q, "bell", 0.05), t); t += d * q
    elif mood == "paskah":
        for i, ch in enumerate([[60,64,67],[65,69,72],[67,71,74],[60,64,67]] * 3):
            t0 = i * 2.6
            if t0 >= dur: break
            for n in ch: put(b, tone(hz(n), 2.8, "pad", 0.06), t0)
            put(b, tone(hz(ch[2] + 12), 2.0, "piano", 0.08), t0 + 0.6)
    elif mood == "imlek":  # pentatonik G: G A B D E
        sc = [67, 69, 71, 74, 76, 79, 81]; beat = 60 / 96
        put(b, tone(hz(43), 3.0, "gong", 0.25), 0.05)
        for i in range(int(dur / beat)):
            put(b, tone(hz(sc[int(rng.integers(0, len(sc)))]), beat * 1.5, "pluck", 0.13), i * beat)
            if i % 8 == 0 and i: put(b, tone(hz(43), 3.0, "gong", 0.15), i * beat)
            if i % 2 == 0: put(b, drum("kick", 0.12), i * beat)
    elif mood == "nyepi":  # pelog kira-kira
        sc = [64, 65, 67, 71, 72]; beat = 1.0
        put(b, tone(hz(40), dur, "pad", 0.04), 0)
        for i in range(int(dur / beat)):
            put(b, tone(hz(sc[i % len(sc)] + 12), 1.6, "bell", 0.07), i * beat)
            if i % 4 == 0: put(b, tone(hz(40), 3.5, "gong", 0.14), i * beat)
    elif mood == "waisak":
        put(b, tone(hz(48), dur, "pad", 0.05), 0)
        for i, n in enumerate([72, 76, 79, 76, 74, 72, 67, 72]):
            put(b, tone(hz(n), 3.0, "bell", 0.08), 0.3 + i * 1.3)
            put(b, tone(hz(n - 24), 3.5, "gong", 0.05), 0.3 + i * 2.6)
    elif mood == "nasional":
        bpm = 112; beat = 60 / bpm
        mel = [67, 67, 72, 72, 76, 74, 72, 67, 69, 71, 72, 74, 76, 74, 72, 72]
        prog = [[48,52,55],[53,57,60],[55,59,62],[48,52,55]]
        for i in range(int(dur / beat)):
            put(b, drum("snare" if i % 2 else "kick", 0.2), i * beat)
            if i % 4 == 0:
                for n in prog[(i // 4) % 4]: put(b, tone(hz(n), beat * 4, "brass", 0.05), i * beat)
            put(b, tone(hz(mel[i % len(mel)]), beat * 0.95, "brass", 0.09), i * beat)
    elif mood == "tahunbaru":
        bpm = 118; beat = 60 / bpm
        for i in range(int(dur / beat * 2)):
            t0 = i * beat / 2; ch = CHORDS_MAJ[(i // 8) % 4]
            put(b, tone(hz(ch[i % 3] + 12), beat, "pluck", 0.12), t0)
            if i % 2 == 0: put(b, drum("kick" if i % 4 == 0 else "snare", 0.15), t0)
            put(b, drum("hat", 0.1), t0)
    else:
        raise SystemExit("suasana tidak dikenal: " + mood)
    # reverb sederhana + fade
    out = b.copy()
    for d, g in [(0.05, 0.25), (0.11, 0.18), (0.19, 0.12), (0.29, 0.08)]:
        k = int(d * SR); out[k:] += g * b[:-k]
    t = np.arange(L) / SR
    out *= np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 1.5)
    return out / (np.abs(out).max() + 1e-9) * 0.85

def main():
    img, outp, mood = sys.argv[1], sys.argv[2], sys.argv[3]
    dur = float(sys.argv[4]) if len(sys.argv) > 4 else 10.0
    a = compose(mood, dur)
    with wave.open("/tmp/_ucapan.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a * 32767).astype(np.int16).tobytes())
    fr = int(dur * 30)
    vf = (f"scale=2160:3840,zoompan=z='min(1+0.00025*on,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s=1080x1920:fps=30,"
          f"fade=t=in:st=0:d=0.6,fade=t=out:st={dur-0.8}:d=0.8,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", img, "-i", "/tmp/_ucapan.wav", "-vf", vf,
                    "-t", str(dur), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", outp], check=True)

if __name__ == "__main__":
    main()
