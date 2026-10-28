# takeqa_calibration.py -- the measurements behind takeqa.py's thresholds (29 Oct 2026): motion, brightness and first/middle-frame similarity over the trial clips in C:\Users\punie\Downloads\engine-trial plus synthetic frozen / black clips.
# Run: api/.venv/Scripts/python.exe tools/engine_trials/takeqa_calibration.py   (needs the trial clips on this machine; edit the `tmp` scratch folder below to somewhere writable)
import os, subprocess, sys, glob
sys.path.insert(0, r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api")
import filmcut
exe = filmcut.ffmpeg_exe()
W, H = 64, 36

def sig(path, t):
    r = subprocess.run([exe, "-y", "-ss", f"{max(0.0, t):.3f}", "-i", path, "-frames:v", "1", "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"], capture_output=True)
    return r.stdout if (r.returncode == 0 and len(r.stdout) == W * H) else None

def mad(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)

def metrics(path, n=7):
    d = filmcut.probe_seconds(exe, path)
    if d <= 0: return None
    ts = [d * (0.06 + 0.88 * i / (n - 1)) for i in range(n)]
    sg = [sig(path, t) for t in ts]
    if any(s is None for s in sg): return {"dur": d, "err": "unreadable frame"}
    adj = [mad(a, b) for a, b in zip(sg, sg[1:])]
    span = mad(sg[0], sg[-1])
    lum = [sum(s) / len(s) for s in sg]
    return {"dur": round(d, 2), "adj_min": round(min(adj), 2), "adj_mean": round(sum(adj) / len(adj), 2), "span": round(span, 2), "lum_mean": round(sum(lum) / len(lum), 1), "lum_min": round(min(lum), 1), "mid": sg[n // 2]}

paths = []
for pat in [r"C:\Users\punie\Downloads\engine-trial\coverage_step0\shot_*.mp4", r"C:\Users\punie\Downloads\engine-trial\coverage_step0\a_*.mp4", r"C:\Users\punie\Downloads\engine-trial\flow_trials\omni\**\*.mp4",
            r"C:\Users\punie\Downloads\engine-trial\i2v_*.mp4", r"C:\Users\punie\Downloads\engine-trial\coverage_step0\invalid_text2video\shot_*.mp4"]:
    paths += glob.glob(pat, recursive=True)
res = {}
print("REAL CLIPS")
for p in paths:
    m = metrics(p)
    if not m or "err" in m: print("  skip", os.path.basename(p), m and m.get("err")); continue
    res[p] = m
    print(f"  {os.path.relpath(p, r'C:/Users/punie/Downloads/engine-trial')[:52]:52s} dur={m['dur']:5} adjmin={m['adj_min']:5} adjmean={m['adj_mean']:5} span={m['span']:5} lum={m['lum_mean']:5} lummin={m['lum_min']:5}")

tmp = r"C:\Users\punie\AppData\Local\Temp\claude\C--Users-punie-Heritage-Marketing-Studio-OPUS\188571ea-55a9-4350-b9a0-481c7a9d13b2\scratchpad\qa"
os.makedirs(tmp, exist_ok=True)
src = r"C:\Users\punie\Downloads\engine-trial\coverage_step0\shot_A_1.mp4"
print("SYNTHETIC KNOWN-BAD")
frame = os.path.join(tmp, "f.png"); subprocess.run([exe, "-y", "-ss", "1", "-i", src, "-frames:v", "1", frame], capture_output=True)
for name, args in {
    "frozen_loop": ["-loop", "1", "-i", frame, "-t", "4", "-r", "24", "-c:v", "libx264", "-pix_fmt", "yuv420p"],
    "black": ["-f", "lavfi", "-i", "color=c=black:s=640x360:r=24", "-t", "4", "-c:v", "libx264", "-pix_fmt", "yuv420p"],
    "fade_in_from_black_slow": ["-i", src, "-vf", "fade=t=in:st=0:d=3.5", "-c:v", "libx264", "-pix_fmt", "yuv420p"],
    "dark_scene": ["-i", src, "-vf", "eq=brightness=-0.35", "-c:v", "libx264", "-pix_fmt", "yuv420p"],
}.items():
    out = os.path.join(tmp, name + ".mp4"); subprocess.run([exe, "-y", *args, out], capture_output=True)
    m = metrics(out)
    print(f"  {name:28s}", {k: v for k, v in (m or {}).items() if k != 'mid'})

print("CROSS-SHOT SIMILARITY (mean abs diff of the MIDDLE frames; lower = more alike)")
def mid(p):
    return res[p]["mid"] if p in res else None
base = r"C:\Users\punie\Downloads\engine-trial\coverage_step0"
pairs = [("shot_A_1.mp4", "shot_A_2.mp4"), ("shot_A_1.mp4", "shot_A_3.mp4"), ("shot_A_2.mp4", "shot_A_3.mp4"), ("shot_B_1.mp4", "shot_B_2.mp4"), ("shot_A_1.mp4", "shot_B_1.mp4"),
         ("a_2s_615.mp4", "a_2s_648.mp4"), ("a_1s_677.mp4", "a_2s_615.mp4")]
for a, b in pairs:
    pa, pb = os.path.join(base, a), os.path.join(base, b)
    if pa in res and pb in res: print(f"  {a:14s} vs {b:14s} {mad(res[pa]['mid'], res[pb]['mid']):6.2f}")
# a take against ITSELF (a re-roll of the same frame should be alike) and against a slightly shifted copy
p = os.path.join(base, "shot_A_1.mp4"); print("  same clip vs itself", round(mad(res[p]['mid'], res[p]['mid']), 2))
