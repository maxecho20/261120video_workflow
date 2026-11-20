---
name: talking-head-edit
description: 按口播语义删留片段，并把字幕、关键词和辅助画面合成可编辑视频。
---

# talking-head-edit

先读 speech-transcription 产出的 transcript.json。按照讲述意图选择完整句子，把保留的片段原样写入 `workspace_data/edl_cuts.json` 的 keep_segments 数组；保留 id/text/start/end。脚本未收到 EDL 时只过滤纯语气词，不会自动判断语义重说，不能把默认行为说成智能精剪。

按 `docs/data-contracts.md` 写 storyboard.json。先确定剪后时间和字幕，再安排 B-roll；start_s/end_s 指剪后时间。B-roll 内部入点由 Agent 先裁出可用片段。现有渲染器的 B-roll_overlay 默认全屏覆盖且静音；需要小窗、三例同屏或素材原音，修改任务内的 src/MainVideo.tsx 并实际检查，不要只写一个它不识别的字段。

运行 `python3 scripts/run_talk.py render --run runs/my-talk --storyboard runs/my-talk/storyboard.json --assets input/material/broll`。保持人声可听、字幕可读，检查关键词与原话一致。先渲短段；更改稿件时保留旧输出，再交由 video-review 检查。
