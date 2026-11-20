"""Validate streams, duration alignment and full decode; not an aesthetic review."""
import argparse
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('video', type=Path)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--allow-silent', action='store_true')
a = p.parse_args()
d = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(a.video)]))
v = next((s for s in d['streams'] if s['codec_type'] == 'video'), None)
au = next((s for s in d['streams'] if s['codec_type'] == 'audio'), None)
errors = []
if not v:
    errors.append('缺少视频轨')
if not au and not a.allow_silent:
    errors.append('缺少音轨')
if v and au and 'duration' in v and 'duration' in au:
    if abs(float(v['duration']) - float(au['duration'])) > 0.15:
        errors.append('音视频时长相差超过 0.15 秒')
decode = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(a.video), '-f', 'null', '-'], capture_output=True, text=True)
if decode.returncode or decode.stderr.strip():
    errors.append('完整解码报错：' + decode.stderr.strip())
result = {'file': a.video.name, 'duration_s': float(d['format'].get('duration', 0)), 'ok': not errors, 'errors': errors,
          'streams': [{k: s[k] for k in ['codec_type', 'width', 'height', 'duration', 'nb_frames'] if k in s} for s in d['streams']],
          'scope': '文件与解码检查；画面和声音观感仍需实际观看、试听'}
a.out.parent.mkdir(parents=True, exist_ok=True)
a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
raise SystemExit(0 if result['ok'] else 1)
