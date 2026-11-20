"""Package only the reviewed text/code allowlist, never runtime assets or history."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('output', type=Path)
a = p.parse_args()
names = json.loads((root / 'release-files.json').read_text())
assert len(names) == len(set(names)), '发布清单存在重复项'
forbidden = re.compile(r'/Users/|/home/|feishu\.(?:cn|com)|doubao\.com/docx|carl-wechat-writer|khazix-writer|(?:sk-|ghp_)[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----')
allowed = {'.md', '.txt', '.json', '.py', '.ts', '.tsx'}
contents = {}
for name in names:
    rel = Path(name)
    assert not rel.is_absolute() and '..' not in rel.parts, name
    path = root / rel
    assert path.is_file() and not path.is_symlink(), name
    assert all(not q.is_symlink() for q in path.parents if q != root.parent), name
    assert path.suffix in allowed or name in {'.gitignore', 'VERSION', 'input/material/.gitkeep'}, name
    data = path.read_bytes()
    text = data.decode('utf-8')
    # This script itself contains detection patterns, not credentials or private material.
    if name != 'scripts/build_release.py':
        assert not forbidden.search(text), '请检查隐私内容：' + name
    contents[name] = data
manifest = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in sorted(contents.items()))
a.output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(a.output, 'w', zipfile.ZIP_DEFLATED) as z:
    for name, data in sorted(contents.items()):
        z.writestr('ai-video-workflow-kit/' + name, data)
    z.writestr('ai-video-workflow-kit/MANIFEST.sha256', manifest)
print(json.dumps({'files': len(contents), 'zip_bytes': a.output.stat().st_size, 'sha256': hashlib.sha256(a.output.read_bytes()).hexdigest()}, indent=2))
