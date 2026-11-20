---
name: speech-transcription
description: 把真人口播转成带时间戳和逐词信息的文本，校对术语后交给剪辑。
---

# speech-transcription

先在任务目录准备 input/raw_video.mp4；可从根目录运行 `python3 scripts/run_talk.py prepare --source input/material/口播.mp4 --run runs/my-talk`，它会用 faster-whisper/base 生成 `workspace_data/transcript.json`。首次使用会下载开源模型权重。目录必须是新的，避免覆盖已有版本。

对照讲稿和实际原声校对术语、数字、重复录法及句子边界。保留 start/end/id，文字修订后再做剪辑单。ASR 是识别结果，不是自动校对通过。无讲稿仍可转写；低置信度处标出待听审。音乐唱词优先用 music-video 的音轨对齐流程。
