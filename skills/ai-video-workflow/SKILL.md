---
name: ai-video-workflow
description: 统筹视频任务、检查环境并调度工程中的其他视频 Skill。真人口播、产品片、音乐 MV 均从此入口开始。
---

# ai-video-workflow

先读项目 README.md，确认用户要做的片型、受众、时长和输出位置。运行 `python3 scripts/env_check.py --task basic`；正式口播改用 `--task talk`，MV 节拍分析用 `--task mv`。用当前 Python 检查，避免检查一个解释器却用另一个运行。

将任务写入 `runs/<任务名>/brief.md`，素材不移动、不覆盖。按需读取以下同级 Skill：
- media-understanding：先检查素材和代表画面，再决定用哪些。
- speech-transcription：口播转写与术语校对。
- talking-head-edit：按语义剪辑、字幕和辅助画面合成。
- product-video：资料核验、找素材、分镜和产品动效。
- music-video：音轨与歌词、卡点、角色和音乐故事。
- video-review：渲染后检查画面、声音、时长并交付。

初次使用先运行 `python3 scripts/repro_demo.py talk`，验证本机渲染工具能工作。这是程序生成的六秒测试片，不是真人口播实测。正式任务先交带声短预览，根据用户反馈再完成；已经确认过的内容直接继续。保留素材表、分镜、源工程、预览和最终 MP4。
