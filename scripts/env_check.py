"""Check only dependencies required by the selected task, in this interpreter."""
import argparse
import importlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--task', choices=['basic', 'talk', 'mv'], default='basic')
args = parser.parse_args()
checks = []
checks.append({'name': 'Python >= 3.10', 'ok': sys.version_info >= (3, 10), 'version': platform.python_version()})
for name, flag in [('ffmpeg', '-version'), ('ffprobe', '-version'), ('node', '--version'), ('npm', '--version')]:
    path = shutil.which(name)
    try:
        result = subprocess.run([path, flag], capture_output=True, text=True, timeout=20) if path else None
        version = result.stdout.splitlines()[0] if result and result.stdout else ''
        ok = bool(result and result.returncode == 0)
        if name == 'node' and ok:
            ok = int(version.lstrip('v').split('.')[0]) >= 22
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        version, ok = str(error), False
    checks.append({'name': name, 'ok': ok, 'version': version})
for module in {'basic': [], 'talk': ['faster_whisper'], 'mv': ['librosa']}[args.task]:
    try:
        lib = importlib.import_module(module)
        checks.append({'name': module, 'ok': True, 'version': getattr(lib, '__version__', '')})
    except ImportError as error:
        checks.append({'name': module, 'ok': False, 'error': str(error)})
report = {'task': args.task, 'python': sys.executable, 'checks': checks, 'ok': all(c['ok'] for c in checks),
          'node_dependencies_installed': (Path(__file__).resolve().parents[1] / 'node_modules/.bin/remotion').exists()}
print(json.dumps(report, ensure_ascii=False, indent=2))
if not report['ok']:
    print('先安装缺少的系统工具；Python 依赖按任务安装 requirements-talk.txt 或 requirements-mv.txt。')
raise SystemExit(0 if report['ok'] else 1)
