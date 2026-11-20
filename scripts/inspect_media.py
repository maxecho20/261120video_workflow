"""Inventory reader media and extract representative video frames; no semantic inference."""
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('--out', required=True, type=Path)
args = parser.parse_args()
source = args.source.resolve(strict=True)
args.out.mkdir(parents=True, exist_ok=True)
formats = {'.mp4', '.mov', '.mkv', '.webm', '.wav', '.mp3', '.m4a', '.flac', '.png', '.jpg', '.jpeg', '.webp'}
files = [source] if source.is_file() else sorted(p for p in source.rglob('*') if p.is_file() and p.suffix.lower() in formats)
if not files:
    parser.error('没有找到视频、音频或图片，请先放入素材。')
rows = []
for index, path in enumerate(files):
    data = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    duration = float(data['format'].get('duration', 0))
    video = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
    row = {'file': path.name if source.is_file() else str(path.relative_to(source)), 'duration_s': duration,
           'streams': [{k: s[k] for k in ['codec_type', 'codec_name', 'width', 'height', 'sample_rate', 'channels'] if k in s} for s in data['streams']], 'frames': []}
    if video and duration > 0 and path.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp'}:
        for n, position in enumerate([0.1, 0.5, 0.9]):
            frame = args.out / f'{index:03d}-{n}.jpg'
            timestamp = round(duration * position, 3)
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', str(timestamp), '-i', str(path), '-frames:v', '1', '-vf', 'scale=640:-2', str(frame)], check=True)
            row['frames'].append({'seconds': timestamp, 'image': frame.name})
    rows.append(row)
(args.out / 'inventory.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(args.out / 'inventory.json')
