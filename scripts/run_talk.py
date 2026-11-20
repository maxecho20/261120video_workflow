#!/usr/bin/env python3
"""Run the existing speech-editing pipeline in a separate case directory."""
import argparse
import os
import json
from pathlib import Path
import shutil
import subprocess
import sys


def execute(argv, cwd):
    subprocess.run(argv, cwd=cwd, check=True)


def prepare(args, runtime, run):
    source = Path(args.source).resolve(strict=True)
    owned_dirs = ("input", "public", "workspace_data", "out")
    occupied = [name for name in owned_dirs if (run / name).exists() or (run / name).is_symlink()]
    if occupied:
        raise FileExistsError(f"剪辑目录已有运行数据（{', '.join(occupied)}），请另选新的 --run 子目录：{run}")
    # A brief and media inventory may already exist; preserve them, but never reuse pipeline data.
    run.mkdir(parents=True, exist_ok=True)
    for name in owned_dirs:
        (run / name).mkdir()

    clip = run / "input/raw_video.mp4"
    if args.start or args.seconds:
        timing = ["-ss", str(args.start or 0)]
        if args.seconds:
            timing += ["-t", str(args.seconds)]
        execute([
            "ffmpeg", "-nostdin", "-v", "error", "-i", str(source), *timing,
            "-map", "0:v:0", "-map", "0:a:0", "-map_metadata", "-1",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-movflags", "+faststart", str(clip),
        ], run)
    else:
        clip.symlink_to(source)

    execute([sys.executable, str(runtime / "scripts/stage2_whisper.py"), str(clip)], run)
    (run / "source.json").write_text(json.dumps({
        "source": str(source), "start": args.start or 0, "seconds": args.seconds,
        "transcription": "faster-whisper/base",
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"逐字稿：{run / 'workspace_data/transcript.json'}")


def render(args, runtime, run):
    storyboard = Path(args.storyboard).resolve(strict=True)
    assets = Path(args.assets).resolve(strict=True) if args.assets else None
    data = json.loads(storyboard.read_text(encoding="utf-8"))
    for field in ("fps", "width", "height", "segments"):
        if field not in data:
            raise ValueError(f"分镜缺少 {field}")
    for shot in data["segments"]:
        asset = shot.get("b_roll_asset")
        if not asset:
            continue
        asset = Path(asset.removeprefix("assets/"))
        if not assets or asset.is_absolute() or ".." in asset.parts or not (assets / asset).is_file():
            raise ValueError(f"B-roll 未找到：{asset}")

    output = run / "out/final.mp4"
    if output.exists():
        raise FileExistsError(f"成片已存在，先将它存为首版：{output}")
    modules = runtime / "node_modules"
    remotion = modules / ".bin/remotion"
    if not remotion.exists():
        raise FileNotFoundError(f"请在 {runtime} 安装锁文件中的 Node 依赖")

    if not (run / "src").exists():
        shutil.copytree(runtime / "src", run / "src")
    for filename in ("package.json", "package-lock.json", "tsconfig.json"):
        if not (run / filename).exists():
            shutil.copyfile(runtime / filename, run / filename)
    if not (run / "node_modules").is_symlink():
        (run / "node_modules").symlink_to(modules, target_is_directory=True)
    target = run / "public/storyboard.json"
    if storyboard != target:
        shutil.copyfile(storyboard, target)
    if assets and not (run / "public/assets").is_symlink():
        (run / "public/assets").symlink_to(assets, target_is_directory=True)

    execute([sys.executable, str(runtime / "scripts/stage3_video_use.py")], run)
    chrome = os.environ.get("VIDEO_WORKFLOW_CHROME")
    browser = ["--chrome-mode=chrome-for-testing", f"--browser-executable={chrome}"] if chrome else []
    execute([
        str(remotion), "render", "src/index.ts", "MainVideo", str(output),
        "--concurrency=2", "--log=error", *browser,
    ], run)
    execute(["ffmpeg", "-nostdin", "-v", "error", "-i", str(output), "-f", "null", "-"], run)
    print(f"成片已完整解码：{output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline-root", type=Path)
    sub = parser.add_subparsers(dest="step", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--source", required=True)
    prep.add_argument("--run", required=True)
    prep.add_argument("--start", type=float, default=0)
    prep.add_argument("--seconds", type=float)
    final = sub.add_parser("render")
    final.add_argument("--run", required=True)
    final.add_argument("--storyboard", required=True)
    final.add_argument("--assets")

    args = parser.parse_args()
    packaged = Path(__file__).resolve().parents[1] / "runtime"
    runtime = (args.pipeline_root or (packaged if packaged.is_dir() else Path.cwd())).resolve()
    if not (runtime / "scripts/stage2_whisper.py").is_file():
        parser.error("工作目录缺少剪辑运行代码。请用发布包，或指定 --pipeline-root。")
    run = Path(args.run).resolve()
    if args.step == "prepare":
        if args.start < 0 or (args.seconds is not None and args.seconds <= 0):
            parser.error("起点必须非负，片长必须大于零")
        prepare(args, runtime, run)
    else:
        render(args, runtime, run)


if __name__ == "__main__":
    main()
