# 口播与 MV 数据格式

转写：`workspace_data/transcript.json` 包含 duration（秒）及 segments；每段有 id、text、start、end、words，word 有 word/start/end/probability。EDL 的 keep_segments 使用当前转写中要保留的完整段对象，按原时间排序；改词后同步更新 EDL。

剪后字幕由 scripts/stage3_video_use.py 生成 public/aligned_captions.json，含 total_duration 与 captions；字幕已映射到剪后时间，不能继续套原片时间戳。

口播 storyboard 字段见下例；start_s/end_s 使用剪后时间，b_roll_asset 相对 --assets 目录。模板识别 A-roll_zoom_hook、keyword_card、B-roll_overlay；后者目前是全屏静音辅助镜头。小窗或原音需 Agent 修改当前任务内的渲染组件。

```json
{"video_title":"我的视频","fps":30,"width":1920,"height":1080,"segments":[{"segment_id":0,"match_text":"这句要强调","shot_type":"keyword_card","start_s":0,"end_s":2,"camera_scale":[1,1.05],"b_roll_asset":null,"info_card":{"title":"一句话标题","subtitle":"补充信息"},"highlight_keywords":["强调"]}]}
```

MV 计划见 examples/mv-plan.json。clip_start_s/clip_end_s 和事件 start_s/end_s 均为原音轨时间；prepare_mv_timeline.py 转成剪后 start_frame/end_frame。音频必须从同一个 clip_start_s 开始裁切，转时间表不会自动剪音频。demo 里的测试字幕是自写占位句，不是歌曲歌词。
