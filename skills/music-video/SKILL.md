---
name: music-video
description: 分析音乐节拍、对齐歌词并安排镜头与动作，制作短段音乐 MV。
---

# music-video

先检查音乐实际版本、时长、歌词来源、画风和角色。运行 `python3 scripts/beat_map.py input/material/music.wav runs/my-mv/beats.json` 获取候选节拍与音头；无 librosa 时可用 WAV + NumPy/SciPy 的 --onsets-only，只产音头候选，不冒充重拍。

唱词识别可能误听。结合用户歌词与实际音轨校对，不能直接套其他版本的时间戳。将选段、lyric/scene/cue 事件写成 `examples/mv-plan.json` 的格式，用 `python3 scripts/prepare_mv_timeline.py runs/my-mv/plan.json runs/my-mv/timeline.json` 转换成片内帧数；修改选段后重新换算。

`examples/index.tsx` 的 MusicDemo 仅演示按时间表切画面和字幕。根据用户创意写任务场景；保持角色与色板一致，让具体动作而非整张图片平移承担叙事。先做一小段带声预览，试听副歌切换，检查手脚接触、遮挡、连续性及歌词可读性。简单流程跑通不等于精细动画过关。
