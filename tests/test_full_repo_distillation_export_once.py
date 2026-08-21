import base64
import hashlib
import json
import sys
import unittest
from pathlib import Path


class FullRepoDistillationEvidenceExport(unittest.TestCase):
    def test_export_repository_evidence_to_log(self):
        root = Path(__file__).resolve().parents[1]
        excluded_roots = {'.git', '.reasoning-distiller', 'project-knowledge'}
        excluded_paths = {
            '.github/workflows/full-repo-distillation-export-once.yml',
            'tests/test_full_repo_distillation_export_once.py',
        }

        entries = []
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(root).as_posix()
            if rel.split('/', 1)[0] in excluded_roots or rel in excluded_paths:
                continue
            data = path.read_bytes()
            entries.append({
                'path': rel,
                'bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest(),
            })

        sys.stdout.write('\nRD_EVIDENCE_MANIFEST_BEGIN\n')
        sys.stdout.write(json.dumps({
            'contract': 'reasoning-distiller-repository-evidence-log/1',
            'base_commit': 'eb25ed17b11fcf346b329c6280abcaf389100c2c',
            'file_count': len(entries),
            'total_bytes': sum(e['bytes'] for e in entries),
            'files': entries,
        }, sort_keys=True))
        sys.stdout.write('\nRD_EVIDENCE_MANIFEST_END\n')

        for entry in entries:
            rel = entry['path']
            data = (root / rel).read_bytes()
            header = json.dumps(entry, sort_keys=True)
            sys.stdout.write(f'RD_EVIDENCE_FILE_BEGIN {header}\n')
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                sys.stdout.write('RD_EVIDENCE_ENCODING base64\n')
                sys.stdout.write(base64.b64encode(data).decode('ascii') + '\n')
            else:
                sys.stdout.write('RD_EVIDENCE_ENCODING utf-8\n')
                sys.stdout.write(text)
                if text and not text.endswith('\n'):
                    sys.stdout.write('\n')
            sys.stdout.write(f'RD_EVIDENCE_FILE_END {json.dumps(rel)}\n')

        sys.stdout.flush()
        self.assertGreater(len(entries), 0)


if __name__ == '__main__':
    unittest.main()
