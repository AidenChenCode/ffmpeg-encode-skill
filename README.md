# ffmpeg-encode — 编码层 Claude Code Skill

> Encode layer of a code-generated video pipeline: one script turns a PNG sequence + WAV into an H.264 master (crf 17) and a web version (crf 24), or WebM / ProRes / GIF; also mux-only, audio-only, gain, scaling and cropping — plus a recipes sheet for trimming, concatenation, subtitles, contact sheets, spectrograms and probing.

技术栈五层里的**编码**层。参数一次定好（yuv420p、High 4.1、bt709、faststart、AAC 192k、关键帧 2 s），不再手敲长命令。

## 安装

```bash
git clone https://github.com/AidenChenCode/ffmpeg-encode-skill.git ~/.claude/skills/ffmpeg-encode
```
需要 ffmpeg / ffprobe。

## 使用

```bash
python3 ~/.claude/skills/ffmpeg-encode/scripts/encode.py --meta build/meta.json --out out/name.mp4 --web
python3 ~/.claude/skills/ffmpeg-encode/scripts/encode.py --frames build/frames/f_%04d.png --fps 30 --audio build/audio.wav --out out/name.mp4
python3 ~/.claude/skills/ffmpeg-encode/scripts/encode.py --out out/name.gif --frames ... --fps 15 --scale 960:-2
python3 ~/.claude/skills/ffmpeg-encode/scripts/encode.py --mux video.mp4 --audio music.wav --out final.mp4
```

## 结构

```
SKILL.md                 工作流与参数取舍
scripts/encode.py        mp4 / webm / prores / gif / mux / audio-to
references/recipes.md    截取、拼接、缩放竖版、音频、抽帧拼图、频谱、字幕叠加、批处理
```

## 同一套技术栈的其它 skill

| 层 | 仓库 |
|---|---|
| 画面 | [webgl-canvas-scene-skill](https://github.com/AidenChenCode/webgl-canvas-scene-skill) |
| 音乐 | [webaudio-score-skill](https://github.com/AidenChenCode/webaudio-score-skill) |
| 导出 | [headless-export-skill](https://github.com/AidenChenCode/headless-export-skill) |
| 编码 | ffmpeg-encode-skill（本仓库） |
| 核对 | [video-verify-skill](https://github.com/AidenChenCode/video-verify-skill) |
| 组合体 | [motion-graphics-skill](https://github.com/AidenChenCode/motion-graphics-skill) |
