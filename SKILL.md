---
name: ffmpeg-encode
description: "编码层：用 ffmpeg 把 PNG 序列 + WAV 编成 MP4（libx264 crf17 母版 + crf24 网络版、AAC 192k、yuv420p、bt709、faststart）、WebM、ProRes 或 GIF；也做只混流、只转音频、加减响度、缩放/裁切、拼接、截取。当用户提到'ffmpeg''编码成 MP4''压成网络版''导出 GIF/WebM/ProRes''合并音视频''改码率/分辨率/帧率''视频太大压小''转竖版''截一段''拼接几段'等时触发；任何代码生成视频流程的编码步骤也用本 skill。"
---

# ffmpeg 编码层

目标：把上游产物（PNG 序列、WAV）变成可交付的文件，参数一次定好、不再手敲长命令。

## 上下游

- 上游：`headless-export`（`build/frames/f_%04d.png` + `build/audio.wav` + `build/meta.json`）或任何图片序列/视频/音频。
- 下游：`video-verify`（核对帧数、响度、同步）。

## 工作流

```bash
python3 <skill>/scripts/encode.py --meta <dir>/build/meta.json --out <dir>/out/name.mp4 --web
```
`--meta` 自动取帧率（含 `--step` 折算）、帧目录、音频。没有 meta 就显式给：`--frames build/frames/f_%04d.png --fps 30 --audio build/audio.wav`。

产物：`name.mp4`（crf 17 母版，逐帧颗粒会让它很大）与 `name_web.mp4`（crf 24，几 MB，交付用；音频直接复制）。

其它：
- 响度微调：`--gain -2`（dB；先用 video-verify 量）
- 其它容器：`--out x.webm`（VP9 + Opus）、`--out x.mov --format prores`（ProRes HQ）、`--out x.gif`（两遍调色板，建议先 `--scale 960:-2`）
- 缩放/竖版：`--scale 1080:-2`；裁切成 9:16：`--vf "crop=ih*9/16:ih"`
- 只混流：`--mux video.mp4 --audio audio.wav --out final.mp4`（画面不重编码）
- 只转音频：`--audio build/audio.wav --audio-to out/music.m4a`（或 .mp3）
- 母版质量：`--crf 17 --preset slow`（默认）；更小：`--crf 20`

其它场景的现成命令（截取、拼接、加字幕、抽帧、频谱、探测）见 `references/recipes.md`。

## 参数为什么这么定

- `yuv420p` + `-profile:v high -level 4.1` + `+faststart`：所有播放器/平台都能放，网页可边下边播。
- 关键帧 `keyint = 2 s`：拖动流畅、体积可控。
- bt709 三个 color 标签写全：不同播放器颜色一致，避免"发灰/偏色"。
- 网络版从母版转而不是从 PNG 再编一遍：省一半时间，画质差异肉眼不可见。
- 音频 AAC 192k 48 kHz：视频平台标准；WAV 直接嵌入会被平台重编码，没必要。

## 文件

```
scripts/encode.py        统一入口（mp4 / webm / prores / gif / mux / audio-to）
references/recipes.md    截取、拼接、叠字幕、抽帧拼图、频谱图、探测、批处理
```
