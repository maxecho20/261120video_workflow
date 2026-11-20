import json
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


FILLER_ONLY = re.compile(r"(?:呃|啊|嗯|额|唔|那个|就是说)+")


def build_timeline(segments, keep_ids, duration, max_silence_gap, padding):
    # All source and output calculations use integer milliseconds.
    bounds = [(round(seg["start"] * 1000), round(seg["end"] * 1000)) for seg in segments]
    gap_ms = round(max_silence_gap * 1000)
    padding_ms = round(padding * 1000)
    duration_ms = round(duration * 1000)

    groups = []
    for index, segment in enumerate(segments):
        if segment["id"] not in keep_ids:
            continue
        start, end = bounds[index]
        if not 0 <= start < end <= duration_ms:
            raise ValueError(f"转录片段 {segment['id']} 的时间范围无效")
        if groups and groups[-1][-1] == index - 1 and start - bounds[index - 1][1] <= gap_ms:
            groups[-1].append(index)
        else:
            groups.append([index])

    intervals = []
    captions = []
    cursor = 0
    for group in groups:
        first, last = group[0], group[-1]
        first_start = bounds[first][0]
        last_end = max(bounds[index][1] for index in group)
        start = max(0, first_start - padding_ms)
        end = min(duration_ms, last_end + padding_ms)
        # A cut's breathing room may contain silence, but must not restore a rejected sentence.
        # Neighboring kept ranges can share at most half the gap each.
        if first > 0:
            left_boundary = bounds[first - 1][1]
            if segments[first - 1]["id"] in keep_ids:
                left_boundary = (left_boundary + first_start) // 2
            start = max(start, min(first_start, left_boundary))
        if last + 1 < len(segments):
            right_boundary = bounds[last + 1][0]
            if segments[last + 1]["id"] in keep_ids:
                right_boundary = (right_boundary + last_end) // 2
            end = min(end, max(last_end, right_boundary))

        intervals.append((start, end))
        for index in group:
            segment = segments[index]
            caption_start = start if index == first else bounds[index][0]
            caption_end = end if index == last else min(bounds[index][1], bounds[index + 1][0])
            if caption_end <= caption_start:
                continue
            offset = cursor - start
            words = []
            for word in segment.get("words", []):
                word_start = max(caption_start, round(word["start"] * 1000))
                word_end = min(caption_end, round(word["end"] * 1000))
                if word["word"].strip() and word_start <= word_end:
                    words.append({
                        "word": word["word"],
                        "start": (word_start + offset) / 1000,
                        "end": (word_end + offset) / 1000,
                    })

            captions.append({
                "segment_id": segment["id"],
                "text": segment["text"],
                "start": (caption_start + offset) / 1000,
                "end": (caption_end + offset) / 1000,
                "words": words,
            })
        cursor += end - start

    if not intervals:
        raise ValueError("没有可保留的口播片段，请检查转录或 edl_cuts.json")
    return intervals, {"total_duration": cursor / 1000, "captions": captions}


def process_rough_cut(
    raw_video="input/raw_video.mp4",
    transcript_path="workspace_data/transcript.json",
    edl_path="workspace_data/edl_cuts.json",
    output_video="public/rough_cut.mp4",
    aligned_captions_path="public/aligned_captions.json",
    max_silence_gap=0.4,
    padding=0.10,
):
    transcript = json.loads(Path(transcript_path).read_text(encoding="utf-8"))
    segments = sorted(transcript["segments"], key=lambda seg: seg["start"])
    edl = Path(edl_path)
    generate_edl = not edl.exists()
    if generate_edl:
        keep_segments = []
        for seg in segments:
            clean_text = re.sub(r"[^\w]+", "", seg["text"])
            if clean_text and not FILLER_ONLY.fullmatch(clean_text):
                keep_segments.append(seg)
    else:
        keep_segments = json.loads(edl.read_text(encoding="utf-8"))["keep_segments"]
        by_id = {seg["id"]: seg for seg in segments}
        for keep in keep_segments:
            source = by_id.get(keep["id"])
            if source is None or any(keep.get(key) != source[key] for key in ("text", "start", "end")):
                raise ValueError(f"EDL 片段 {keep['id']} 与当前转录不匹配，请按当前转录更新 EDL")

    intervals, aligned = build_timeline(
        segments, {seg["id"] for seg in keep_segments}, transcript["duration"], max_silence_gap, padding,
    )

    # Keep source video frames on the same millisecond offset as the audio cuts.
    # Joint A/V concat would advance by the longer stream in each clip, accumulating frame rounding.
    video_ranges = []
    removed_time = []
    previous_end = 0
    filters = []
    for index, (start, end) in enumerate(intervals):
        times = f"start={start / 1000:.3f}:end={end / 1000:.3f}"
        filters.append(f"[0:a:0]atrim={times},asetpts=PTS-STARTPTS[a{index}]")
        video_ranges.append(f"gte(pts,{start * 1000})*lt(pts,{end * 1000})")
        removed_time.append(f"{(start - previous_end) * 1000}*gte(PTS,{start * 1000})")
        previous_end = end

    keep_frames = "+".join(video_ranges)
    removed_pts = "+".join(removed_time)
    audio_inputs = "".join(f"[a{index}]" for index in range(len(intervals)))
    duration = aligned["total_duration"]
    filters.extend([
        f"[0:v:0]settb=AVTB,select='{keep_frames}',setpts='if(eq(N,0),0,PTS-({removed_pts}))',"
        "eq=contrast=1.06:saturation=1.10:brightness=0.02,vignette=PI/10,format=yuv420p[vout]",
        f"{audio_inputs}concat=n={len(intervals)}:v=0:a=1[acat]",
        f"[acat]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,"
        f"apad=whole_dur={duration:.3f},atrim=duration={duration:.3f}[aout]",
    ])

    destination = Path(output_video)
    captions_file = Path(aligned_captions_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    captions_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"[Stage 3: video-use] 正在粗剪与调色，共合并 {len(intervals)} 个片段", flush=True)
    with TemporaryDirectory(dir=destination.parent) as temp:
        cut = Path(temp) / "rough_cut.mp4"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", str(raw_video),
            "-filter_complex", ";".join(filters), "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-fps_mode", "vfr", "-enc_time_base:v", "1:90000",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(cut),
        ], check=True)
        cut.replace(destination)

    captions_file.write_text(json.dumps(aligned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if generate_edl:
        edl.parent.mkdir(parents=True, exist_ok=True)
        edl.write_text(
            json.dumps({"keep_segments": keep_segments}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"[Stage 3: video-use] 输出完成: {destination} ({aligned['total_duration']}s)")


if __name__ == "__main__":
    process_rough_cut()
