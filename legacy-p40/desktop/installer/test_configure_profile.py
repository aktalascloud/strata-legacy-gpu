import importlib.util
import json
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name('configure_profile.py')
spec = importlib.util.spec_from_file_location('configure_profile', SCRIPT)
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)


class ConfigureProfileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='strata-installer-test-')
        self.base = Path(self.tmp.name)
        self.root = self.base / 'install'
        self.model = self.base / 'user-model'
        self.model.mkdir()
        for name in ('Swift-IQ3_S-00001-of-00002.gguf', 'Swift-IQ3_S-00002-of-00002.gguf'):
            (self.model / name).write_bytes(name.encode())
        control = self.root / 'app' / 'control'
        (control / 'data').mkdir(parents=True)
        (control / 'data' / 'expert-profile.bin').write_bytes(b'expert-profile')
        (self.root / 'tools').mkdir()
        shutil.copyfile(Path(__file__).with_name('make_profile.py'), self.root / 'tools' / 'make_profile.py')
        for name in ('cuda', 'vision'):
            (self.root / name).mkdir()
        engine = self.root / 'components' / 'engine' / 'local'
        engine.mkdir(parents=True)
        files = []
        for name in ('strata.exe', 'strata_kq.dll', 'strata-vision.exe'):
            target = engine / name
            target.write_bytes(name.encode())
            files.append({'path': name, 'sha256': cfg.file_hash(target), 'bytes': target.stat().st_size})
        (engine / 'engine-component.json').write_text(json.dumps({
            'id': 'strata-engine', 'backend': 'cuda', 'platform': 'windows-x86_64',
            'archs': ['sm_61'], 'entrypoint': 'strata.exe', 'files': files,
        }), encoding='utf-8')
        self.builds = 0

    def tearDown(self):
        self.tmp.cleanup()

    def builder(self, _root, _shard, pack):
        self.builds += 1
        (pack / 'tokenizer').mkdir(parents=True)
        for name in ('dense.bin', 'index.txt', 'native_experts.txt', 'tokenizer/chat_template.jinja',
                     'tokenizer/vocab.json', 'tokenizer/merges.txt', 'tokenizer/token_type.json'):
            (pack / name).write_bytes(b'fixture')

    def configure(self, mtp=None, **overrides):
        opts = {'build_pack': self.builder, 'disk_free': lambda _p: 100 * 1024**3}
        opts.update(overrides)
        return cfg.configure(self.root, self.model, mtp, **opts)

    def profile(self):
        return json.loads((self.root / 'install' / 'strata-swift-1.5-iq3-s.json').read_text(encoding='utf-8'))

    def test_no_mtp_creates_complete_model_free_local_profile(self):
        report = self.configure()
        self.assertEqual(report['mtp'], 'off')
        self.assertEqual(report['vision'], 'off')
        profile = self.profile()
        self.assertEqual(profile['exe'], 'component:strata-engine')
        self.assertEqual(profile['host'], '127.0.0.1')
        self.assertEqual(profile['port'], 8093)
        self.assertEqual(profile['api_key'], 'none')
        self.assertEqual(profile['parallel'], 1)
        self.assertEqual(profile['ui_resource_profile'], 'performance')
        self.assertEqual(json.loads((self.root / 'shell-prefs.json').read_text(encoding='utf-8')),
                         {'port': 0, 'tray': True, 'language': 'ru'})
        self.assertEqual(profile['user_args'], profile['args'])
        self.assertEqual((self.root / 'install' / 'models-directory.txt').read_text(encoding='utf-8').strip(), str(self.model.resolve()))
        uniform = Path(profile['args'][profile['args'].index('--expert-profile') + 1])
        self.assertEqual(cfg.file_hash(uniform), cfg.UNIFORM_SHA256)
        self.assertIn('uniform-no-traces', report['expert_profile'])
        for flag, expected in [('--max-context', '262144'), ('--kv', 'q4_0'), ('--prefill', '1536'),
                               ('--vram-reserve-mib', '210'), ('--pool-workers', '14')]:
            self.assertEqual(profile['args'][profile['args'].index(flag) + 1], expected)
        self.assertNotIn('--mtp', profile['args'])
        self.assertNotIn('--spec', profile['args'])
        self.assertEqual(self.builds, 1)
        self.assertTrue((self.root / 'models' / 'swift-iq3_s' / 'local-swift-source.json').is_file())

    def test_existing_prepared_q2_mtp_and_vision_are_selected_without_copying(self):
        mtp = self.base / 'existing-mtp'
        mtp.mkdir()
        for name in cfg.MTP_FILES:
            (mtp / name).write_bytes(b'1234567890123456' if name == 'experts.bin' else b'abcd')
        (self.model / 'mmproj-Qwen3.8-Flash-Next-BF16.gguf').write_bytes(b'vision')
        with mock.patch.object(cfg, 'MTP_EXPERT_BYTES', 16):
            report = self.configure(mtp)
        self.assertEqual(report['mtp'], 'q2')
        self.assertEqual(report['vision'], 'cpu-16')
        profile = self.profile()
        self.assertEqual(profile['args'][profile['args'].index('--mtp') + 1], str(mtp.resolve()))
        self.assertEqual(profile['ui_resource_profile'], 'performance')
        self.assertEqual(profile['user_args'], profile['args'])
        for flag, expected in [('--max-context', '262144'), ('--kv', 'q4_0'), ('--prefill', '1536'),
                               ('--vram-reserve-mib', '210'), ('--pool-workers', '14'), ('--spec', '3')]:
            self.assertEqual(profile['args'][profile['args'].index(flag) + 1], expected)
        self.assertEqual(profile['vision']['threads'], 16)
        self.assertFalse(profile['vision']['gpu'])
        self.assertEqual((mtp / 'experts.bin').read_bytes(), b'1234567890123456')

    def test_wrong_mtp_fails_without_creating_profile_or_pack(self):
        mtp = self.base / 'wrong-mtp'
        mtp.mkdir()
        for name in cfg.MTP_FILES:
            (mtp / name).write_bytes(b'not-a-q2-pack')
        with self.assertRaisesRegex(ValueError, 'подготовленным набором Q2'):
            self.configure(mtp)
        self.assertFalse((self.root / 'install' / 'strata-swift-1.5-iq3-s.json').exists())
        self.assertFalse((self.root / 'models' / 'swift-iq3_s').exists())

    def test_insufficient_space_does_not_start_preparation(self):
        with self.assertRaisesRegex(OSError, 'Недостаточно места'):
            self.configure(disk_free=lambda _p: 0)
        self.assertEqual(self.builds, 0)

    def test_different_existing_model_directory_is_retained_before_pack(self):
        directory = self.root / 'install'
        directory.mkdir()
        marker = directory / 'models-directory.txt'
        marker.write_text('someone-else\n', encoding='utf-8')
        with self.assertRaisesRegex(FileExistsError, 'путь моделей сохранён'):
            self.configure()
        self.assertEqual(marker.read_text(encoding='utf-8'), 'someone-else\n')
        self.assertEqual(self.builds, 0)
        self.assertFalse((self.root / 'models' / 'swift-iq3_s').exists())

    def test_existing_profile_and_unknown_pack_are_never_overwritten(self):
        config_dir = self.root / 'install'
        config_dir.mkdir()
        profile = config_dir / 'strata-swift-1.5-iq3-s.json'
        profile.write_text('existing', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            self.configure()
        self.assertEqual(profile.read_text(encoding='utf-8'), 'existing')
        profile.unlink()
        pack = self.root / 'models' / 'swift-iq3_s'
        pack.mkdir(parents=True)
        (pack / 'keep').write_text('keep', encoding='utf-8')
        with self.assertRaisesRegex(FileExistsError, 'Существующий набор сохранён'):
            self.configure()
        self.assertEqual((pack / 'keep').read_text(encoding='utf-8'), 'keep')

    def test_неполный_pack_is_not_published(self):
        def неполный(_root, _shard, dest):
            dest.mkdir(parents=True)
            (dest / 'dense.bin').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError, 'неполный'):
            self.configure(build_pack=неполный)
        self.assertFalse((self.root / 'models' / 'swift-iq3_s').exists())
        self.assertFalse((self.root / 'install' / 'strata-swift-1.5-iq3-s.json').exists())
        self.assertFalse((self.root / 'install' / '.swift-configure.lock').exists())

    def test_changed_or_ambiguous_engine_is_rejected(self):
        (self.root / 'components' / 'engine' / 'local' / 'strata_kq.dll').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'целый компонент движка CUDA'):
            self.configure()
        self.assertEqual(self.builds, 0)


if __name__ == '__main__':
    unittest.main()
