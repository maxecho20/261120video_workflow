---
name: media-understanding
description: 整理视频、音频、图片的规格与代表帧，供 Agent 判断画面含义、素材用途和剪辑入点。
---

# media-understanding

运行 `python3 scripts/inspect_media.py input/material --out runs/<任务名>/media`。报告包含规格、时长和视频代表帧；脚本不自动理解语义，也不保证均匀抽帧能抓到全部关键动作。

实际查看图片和抽帧，视频相关细节需回到对应片段播放或补帧，音轨需试听。把观察到的内容、适用镜头和入出点写到素材表。图片是否可用还要看清晰度、方向和裁切；不要把文件名当成内容证据。联网素材由 product-video 核对出处及使用条件。
