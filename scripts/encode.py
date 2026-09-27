#!/usr/bin/env python3
"""编码层：PNG 序列 (+ WAV) → MP4 / WebM / ProRes / GIF；或只混流、只转音频。
用法
  python3 encode.py --meta build/meta.json --out out/name.mp4 [--web]          # 从 headless-export 的 meta.json 取帧率/帧目录/音频
  python3 encode.py --frames build/frames/f_%04d.png --fps 30 --audio build/audio.wav --out out/name.mp4 [--web]
选项
  --web              另出一版 crf 24 的网络版（<out>_web.mp4，音频直接复制）
  --crf 17 --preset slow      母版质量（默认 crf 17 / slow）
  --gain -2          编码时给音频加/减 dB（响度微调）
  --format mp4|webm|prores|gif   默认按 --out 后缀判断
  --scale 1280:-2    输出前缩放（如 4K→1080p、横→竖裁切用 --vf 自定义）
  --vf "<filter>"    附加视频滤镜
  --loop-audio       音频比画面短时循环补齐（默认 -shortest 截到较短者）
  --mux VIDEO        不重编码画面：把 VIDEO 与 --audio 混流成 --out
  --audio-to out.m4a|out.mp3   只转音频（WAV → AAC/MP3 192k）
"""
import argparse, json, os, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument('--meta'); ap.add_argument('--frames'); ap.add_argument('--fps', type=float); ap.add_argument('--audio')
ap.add_argument('--out'); ap.add_argument('--web', action='store_true'); ap.add_argument('--crf', type=int, default=17); ap.add_argument('--preset', default='slow')
ap.add_argument('--gain'); ap.add_argument('--format'); ap.add_argument('--scale'); ap.add_argument('--vf'); ap.add_argument('--loop-audio', action='store_true')
ap.add_argument('--mux'); ap.add_argument('--audio-to')
a = ap.parse_args()

def run(cmd):
    print('ffmpeg', ' '.join(cmd))
    r = subprocess.run(['ffmpeg', '-v', 'error', '-stats', *cmd])
    if r.returncode != 0: sys.exit('ffmpeg failed')
def size(p): return f"{os.path.getsize(p) / 1e6:.1f} MB"

# ---- 只转音频
if a.audio_to:
    src = a.audio or sys.exit('--audio-to 需要 --audio')
    codec = ['-c:a', 'libmp3lame', '-b:a', '192k'] if a.audio_to.endswith('.mp3') else ['-c:a', 'aac', '-b:a', '192k']
    os.makedirs(os.path.dirname(os.path.abspath(a.audio_to)), exist_ok=True)
    run(['-y', '-i', src, *codec, a.audio_to]); print(f"→ {a.audio_to} ({size(a.audio_to)})"); sys.exit(0)

# ---- 只混流
if a.mux:
    if not (a.out and a.audio): sys.exit('--mux 需要 --audio 与 --out')
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    run(['-y', '-i', a.mux, '-i', a.audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', a.out])
    print(f"→ {a.out} ({size(a.out)})"); sys.exit(0)

# ---- 从 meta.json 补默认值
fps, frames, audio = a.fps, a.frames, a.audio
if a.meta:
    m = json.load(open(a.meta)); mdir = os.path.dirname(os.path.abspath(a.meta))
    fps = fps or m['FPS'] / (m.get('step') or 1)
    frames = frames or os.path.join(mdir, 'frames', 'f_%04d.png')
    if audio is None and m.get('hasAudio') and os.path.exists(os.path.join(mdir, 'audio.wav')): audio = os.path.join(mdir, 'audio.wav')
if not (fps and frames and a.out): sys.exit('需要 --out 以及 --meta 或 --frames + --fps')
out = a.out; os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
fmt = a.format or os.path.splitext(out)[1].lstrip('.').lower()
vf = ','.join(x for x in [f'scale={a.scale}' if a.scale else None, a.vf] if x)

inputs = ['-y', '-framerate', str(fps), '-i', frames]
if audio: inputs += (['-stream_loop', '-1'] if a.loop_audio else []) + ['-i', audio]
af = ['-af', f'volume={a.gain}dB'] if a.gain else []
common = (['-vf', vf] if vf else []) + (['-shortest'] if audio else [])
color = ['-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709']

if fmt == 'mp4':
    run([*inputs, '-c:v', 'libx264', '-preset', a.preset, '-crf', str(a.crf), '-profile:v', 'high', '-level', '4.1', '-x264-params', f'keyint={int(round(fps * 2))}:min-keyint={int(round(fps))}', *color,
         *af, *(['-c:a', 'aac', '-b:a', '192k', '-ar', '48000'] if audio else []), *common, '-movflags', '+faststart', out])
    print(f"master → {out} ({size(out)})")
    if a.web:
        web = os.path.splitext(out)[0] + '_web.mp4'
        run(['-y', '-i', out, '-c:v', 'libx264', '-preset', a.preset, '-crf', '24', '-profile:v', 'high', '-level', '4.1', *color, '-c:a', 'copy', '-movflags', '+faststart', web])
        print(f"web    → {web} ({size(web)})")
elif fmt == 'webm':
    run([*inputs, '-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0', '-row-mt', '1', '-pix_fmt', 'yuv420p', *af, *(['-c:a', 'libopus', '-b:a', '128k'] if audio else []), *common, out])
    print(f"→ {out} ({size(out)})")
elif fmt in ('prores', 'mov'):
    out = out if out.endswith('.mov') else os.path.splitext(out)[0] + '.mov'
    run([*inputs, '-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', *af, *(['-c:a', 'pcm_s16le'] if audio else []), *common, out])
    print(f"→ {out} ({size(out)})")
elif fmt == 'gif':
    pal = os.path.splitext(out)[0] + '_palette.png'
    gvf = (vf + ',' if vf else '') + 'palettegen=max_colors=128'
    run(['-y', '-framerate', str(fps), '-i', frames, '-vf', gvf, pal])
    run(['-y', '-framerate', str(fps), '-i', frames, '-i', pal, '-lavfi', (vf + ',' if vf else '') + 'paletteuse=dither=bayer:bayer_scale=3', out])
    os.remove(pal); print(f"→ {out} ({size(out)})")
else:
    sys.exit(f'未知格式 {fmt}（mp4 / webm / prores / gif）')
