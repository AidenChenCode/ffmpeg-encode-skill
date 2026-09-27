# ffmpeg 常用配方

都用 `-y` 覆盖输出、`-v error -stats` 只看进度。路径含中文/空格时加引号。

## 探测
```bash
ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels -of json in.mp4
```

## 图片序列 → 视频（encode.py 之外的手写版）
```bash
ffmpeg -y -framerate 30 -i frames/f_%04d.png -i audio.wav -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -level 4.1 \
  -x264-params keyint=60:min-keyint=30 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart out.mp4
```
非连续编号：`-pattern_type glob -i 'frames/*.png'`。

## 网络版 / 再压缩
```bash
ffmpeg -y -i master.mp4 -c:v libx264 -preset slow -crf 24 -pix_fmt yuv420p -c:a copy -movflags +faststart web.mp4
```

## 截取 / 拼接
```bash
ffmpeg -y -ss 8 -to 14 -i in.mp4 -c copy cut.mp4                 # 关键帧对齐的快速截取（可能不精确）
ffmpeg -y -ss 8 -to 14 -i in.mp4 -c:v libx264 -crf 18 -c:a aac cut.mp4    # 精确截取（重编码）
printf "file 'a.mp4'\nfile 'b.mp4'\n" > list.txt && ffmpeg -y -f concat -safe 0 -i list.txt -c copy joined.mp4   # 同参数拼接
```

## 缩放 / 竖版 / 加边
```bash
ffmpeg -y -i in.mp4 -vf "scale=1280:-2" -c:a copy small.mp4
ffmpeg -y -i in.mp4 -vf "crop=ih*9/16:ih" -c:a copy vertical.mp4                  # 中心裁成 9:16
ffmpeg -y -i in.mp4 -vf "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" -c:a copy vertical_pad.mp4   # 横片放进竖版加黑边
```

## 音频
```bash
ffmpeg -y -i in.mp4 -af "volume=-2dB" -c:v copy -c:a aac -b:a 192k out.mp4        # 调音量不动画面
ffmpeg -y -i in.mp4 -af "loudnorm=I=-14:TP=-1:LRA=8" -c:v copy -c:a aac out.mp4   # 一遍式响度归一（精确要两遍）
ffmpeg -i in.mp4 -filter:a ebur128=peak=true -f null -                            # 测响度
ffmpeg -y -i in.mp4 -vn -ac 1 -ar 48000 audio.wav                                 # 抽音轨
ffmpeg -y -i a.wav -c:a aac -b:a 192k a.m4a                                       # WAV → AAC
ffmpeg -y -i video.mp4 -i music.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4   # 换音轨
```

## 抽帧 / 拼图 / 频谱图
```bash
ffmpeg -y -i in.mp4 -vf "fps=1,scale=480:-2,tile=5x3" -q:v 3 sheet_%d.jpg        # 每秒一帧拼图
ffmpeg -y -ss 12.5 -i in.mp4 -frames:v 1 frame.png                                # 某一帧
ffmpeg -y -i in.mp4 -lavfi "showspectrumpic=s=1920x540:legend=1:scale=log" spec.png
ffmpeg -y -i in.mp4 -vf "select='gt(scene,0.3)',showinfo" -vsync vfr -f null - 2>&1 | grep pts_time   # 场景切点
```

## 字幕 / 叠加
```bash
ffmpeg -y -i in.mp4 -vf "drawtext=text='NOVO':fontsize=64:fontcolor=white:x=(w-tw)/2:y=h-120" -c:a copy out.mp4   # 需 ffmpeg 带 freetype
ffmpeg -y -i in.mp4 -i logo.png -filter_complex "overlay=W-w-40:40" -c:a copy out.mp4
ffmpeg -y -i in.mp4 -vf "subtitles=subs.srt" -c:a copy out.mp4
```

## GIF / WebM / ProRes
```bash
ffmpeg -y -i in.mp4 -vf "fps=15,scale=720:-2,palettegen=max_colors=128" pal.png && ffmpeg -y -i in.mp4 -i pal.png -lavfi "fps=15,scale=720:-2,paletteuse=dither=bayer:bayer_scale=3" out.gif
ffmpeg -y -i in.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -row-mt 1 -c:a libopus -b:a 128k out.webm
ffmpeg -y -i in.mp4 -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -c:a pcm_s16le out.mov
```

## 批处理
```bash
for f in *.mov; do ffmpeg -y -i "$f" -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac "${f%.mov}.mp4"; done
```
