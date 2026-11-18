import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


scan = module('scan_payload')
receipt = module('prepare_receipt')
skill = module('install_skill')


class InstallerSourceTests(unittest.TestCase):
    def test_global_skill_is_created_once_without_replacing_user_copy(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / 'defaults' / 'skills' / 'ponytail' / 'SKILL.md'
            source.parent.mkdir(parents=True)
            source.write_bytes(b'fixture skill')
            with mock.patch.object(skill, 'SKILL_SHA256', hashlib.sha256(b'fixture skill').hexdigest()):
                self.assertEqual(skill.install(root), 'installed')
                target = root / 'home' / 'data' / 'skills' / 'ponytail' / 'SKILL.md'
                self.assertEqual(target.read_bytes(), b'fixture skill')
                target.write_bytes(b'user version')
                self.assertEqual(skill.install(root), 'retained')
                self.assertEqual(target.read_bytes(), b'user version')

    def test_skill_hash_mismatch_creates_no_user_skill(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / 'defaults' / 'skills' / 'ponytail' / 'SKILL.md'
            source.parent.mkdir(parents=True)
            source.write_bytes(b'unreviewed')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                skill.install(root)
            self.assertFalse((root / 'home' / 'data' / 'skills' / 'ponytail').exists())

    def test_build_sources_do_not_embed_the_developers_workspace(self):
        # These source files may be committed; the release paths are supplied at invocation.
        forbidden = ('C:' + '\\AI\\', 'C:' + '/AI/', 'C:' + '\\Users\\AI\\')
        for name in ('assemble.ps1', 'build-installer.ps1', 'configure_profile.py', 'prepare_receipt.py', 'start-desktop.ps1.in', 'setup.nsi', 'scan_payload.py'):
            text = Path(__file__).with_name(name).read_text(encoding='utf-8')
            for value in forbidden:
                self.assertNotIn(value.lower(), text.lower(), name)

    def test_scanner_rejects_model_weights_and_private_paths_in_both_encodings(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'good.txt').write_text('no private information', encoding='utf-8')
            self.assertEqual(scan.scan(root, ['Z:\\FixtureRoot\\']), [])
            (root / 'weights.gguf').write_bytes(b'not real weights')
            (root / 'a.exe').write_bytes(b'prefix Z:\\FixtureRoot\\private suffix')
            (root / 'b.exe').write_bytes('Z:/FixtureRoot/private'.encode('utf-16le'))
            (root / 'VCRUNTIME140_1.dll').write_bytes(b'system prerequisite')
            names = {path for path, _ in scan.scan(root, ['Z:\\FixtureRoot\\'])}
            self.assertEqual(names, {'weights.gguf', 'a.exe', 'b.exe', 'VCRUNTIME140_1.dll'})

    def test_vc_receipt_checks_exact_system_copy_on_install(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            windows = root / 'windows'
            system = windows / 'System32' / 'MSVCP140.dll'
            app = root / 'app'
            local = app / 'vision' / system.name
            for file in (system, local):
                file.parent.mkdir(parents=True)
                file.write_bytes(b'fixed system runtime')
            entry = {'path': 'vision/MSVCP140.dll', 'source': 'windows-vc-runtime'}
            with mock.patch.dict(os.environ, {'WINDIR': str(windows)}):
                self.assertEqual(receipt.record(app, entry, fresh=True)['sha256'], receipt.sha256(system))
                system.write_bytes(b'new system runtime')
                self.assertEqual(receipt.record(app, entry)['sha256'], receipt.sha256(local))
                with self.assertRaisesRegex(ValueError, 'differs from System32'):
                    receipt.record(app, entry, fresh=True)

    def test_receipt_is_derived_only_from_install_root_and_hash_manifest(self):
        integrity = {'version': '1', 'build_id': 'fixture',
                     'components': [{'path': 'components/engine/e/strata.exe', 'sha256': 'a' * 64}],
                     'external': [{'path': 'cuda/cudart64_12.dll', 'sha256': 'b' * 64}]}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            result = receipt.receipt(root, integrity)
            self.assertEqual(result['files'][0]['path'], str(root / 'components/engine/e/strata.exe'))
            self.assertEqual(result['external_files'][0]['path'], str(root / 'cuda/cudart64_12.dll'))
            self.assertNotIn('Z:\\FixtureRoot\\', json.dumps(result))
            self.assertEqual(result['external_files'][0]['sha256'], 'b' * 64)


if __name__ == '__main__':
    unittest.main()
