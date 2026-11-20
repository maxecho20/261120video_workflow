from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import wave

from prepare_mv_timeline import prepare_timeline

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "public/repro-demo"
CHOICES = {"talk": "TalkDemo", "product": "ProductDemo", "mv": "MusicDemo"}


def make_score(path):
    sample_rate = 16_000
    notes = (262, 330, 392, 523, 392, 330, 294, 392, 262, 330, 392, 523)
    samples = bytearray()
    for index in range(sample_rate * 6):
        beat, position = divmod(index, sample_rate // 2)
        time = position / sample_rate
        envelope = min(1, time / 0.015) * math.exp(-7 * time)
        value = 8000 * envelope * math.sin(2 * math.pi * notes[beat] * time)
        samples.extend(struct.pack("<h", round(value)))
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
        output.writeframes(samples)


def main():
    parser = argparse.ArgumentParser(description="Export a synthetic, offline reproduction example")
    parser.add_argument("case", choices=tuple(CHOICES))
    selection = parser.parse_args().case
    ffmpeg = shutil.which("ffmpeg")
    remotion = ROOT / "node_modules/.bin" / ("remotion.cmd" if shutil.which("cmd.exe") else "remotion")
    if not ffmpeg or not remotion.is_file():
        parser.error("先安装 FFmpeg，并在项目根目录运行 npm ci")
    ASSETS.mkdir(parents=True, exist_ok=True)
    output = ROOT / "out" / f"demo-{selection}.mp4"
    output.parent.mkdir(exist_ok=True)
    if selection == "talk":
        for filename, source in (("speaker.mp4", "testsrc2"), ("example.mp4", "smptebars")):
            subprocess.run([
                ffmpeg, "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i",
                f"{source}=size=640x360:rate=30", "-t", "6",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(ASSETS / filename),
            ], check=True)
    if selection == "mv":
        plan = json.loads((ROOT / "examples/mv-plan.json").read_text(encoding="utf-8"))
        timeline = prepare_timeline(plan)
        (ASSETS / "mv-timeline.json").write_text(json.dumps(timeline, ensure_ascii=False), encoding="utf-8")
    make_score(ASSETS / "score.wav")
    subprocess.run([
        str(remotion), "render", "examples/index.tsx", CHOICES[selection], str(output),
        "--concurrency=2", "--log=error",
    ], cwd=ROOT, check=True)
    subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-i", str(output), "-f", "null", "-"], check=True)
    print(output)


if __name__ == "__main__":
    main()
