"""Map original-song annotations onto an edited MV's frame clock."""

import argparse
import json
from math import floor, isfinite
from pathlib import Path


def prepare_timeline(plan):
    fps = plan["fps"]
    clip_start = plan["clip_start_s"]
    clip_end = plan["clip_end_s"]
    if type(fps) is not int or fps < 1:
        raise ValueError("fps 必须为正整数")
    if not (isfinite(clip_start) and isfinite(clip_end) and 0 <= clip_start < clip_end):
        raise ValueError("选段时间无效")

    frame_count = floor((clip_end - clip_start) * fps + 0.5)
    if frame_count < 1:
        raise ValueError("选段不足一帧")

    events = []
    event_ids = set()
    for event in plan["events"]:
        event_id, event_type, start = event["id"], event["type"], event["start_s"]
        if not event_id or event_id in event_ids:
            raise ValueError(f"事件 ID 缺失或重复：{event_id}")
        if event_type not in ("cue", "lyric", "scene"):
            raise ValueError(f"{event_id} 的事件类型无效")
        if not clip_start <= start < clip_end:
            raise ValueError(f"{event_id} 的开始时间超出选段")
        event_ids.add(event_id)

        start_frame = floor((start - clip_start) * fps + 0.5)
        result = {**event, "start_frame": min(start_frame, frame_count - 1)}
        if event_type == "cue":
            if "end_s" in event:
                raise ValueError(f"{event_id} 是单点事件，使用 start_s")
        else:
            end = event["end_s"]
            if not start < end <= clip_end:
                raise ValueError(f"{event_id} 的结束时间无效")
            end_frame = floor((end - clip_start) * fps + 0.5)
            if end_frame <= result["start_frame"]:
                raise ValueError(f"{event_id} 在输出时间轴上不足一帧")
            result["end_frame"] = end_frame
        events.append(result)

    return {
        "fps": fps,
        "clip_start_s": clip_start,
        "clip_end_s": clip_end,
        "duration_in_frames": frame_count,
        "events": sorted(events, key=lambda event: event["start_s"]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        timeline = prepare_timeline(json.loads(args.plan.read_text(encoding="utf-8")))
    except (KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
