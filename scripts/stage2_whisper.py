import json
import sys
from pathlib import Path

from faster_whisper import WhisperModel


def transcribe_video(
    video_path="input/raw_video.mp4",
    output_path="workspace_data/transcript.json",
    model_size="base",
):
    print(f"[Stage 2: Whisper] 加载模型 ({model_size}) 并转写: {video_path}", flush=True)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(video_path),
        beam_size=5,
        word_timestamps=True,
    )
    transcript = {
        "language": info.language,
        "duration": round(info.duration, 3),
        "segments": [
            {
                "id": index,
                "text": segment.text.strip(),
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "words": [
                    {
                        "word": word.word.strip(),
                        "start": round(word.start, 3),
                        "end": round(word.end, 3),
                        "probability": round(word.probability, 3),
                    }
                    for word in segment.words or []
                ],
            }
            for index, segment in enumerate(segments)
        ],
    }

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[Stage 2: Whisper] 共识别 {len(transcript['segments'])} 句，已保存至 {destination}")


if __name__ == "__main__":
    transcribe_video(sys.argv[1] if len(sys.argv) > 1 else "input/raw_video.mp4")
