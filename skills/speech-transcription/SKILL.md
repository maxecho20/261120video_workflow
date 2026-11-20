---
name: speech-transcription
description: 把真人口播转成带时间戳和逐词信息的文本，校对术语后交给剪辑。
---

# speech-transcription

从项目根目录运行 `python3 scripts/run_talk.py prepare --source input/material/口播.mp4 --run runs/my-talk`，它会在任务目录准备原片引用 input/raw_video.mp4，并用 faster-whisper/base 生成 `workspace_data/transcript.json`。首次使用会下载开源模型权重。任务目录可以已有简报和素材盘点；如果已有 input、public、workspace_data 或 out 运行目录，请另选新的 --run 子目录，避免覆盖已有版本。

对照讲稿和实际原声校对术语、数字、重复录法及句子边界。保留原始 transcript.json 副本。整段使用时保留 start/end/id；若同段混有重说与有效句，按逐词时间和原声核准的边界拆成互不重叠的短段，为拆分段分配唯一 ID，保留原段映射。同步修订 text 和 words[].word，再从校订稿生成 EDL。末尾疑似多出的字须对照音轨。ASR 是识别结果，不是自动校对通过。无讲稿仍可转写；低置信度处标出待听审。音乐唱词优先用 music-video 的音轨对齐流程。
