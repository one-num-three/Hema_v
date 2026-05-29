from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sanitize_profiles.py"


def load_module():
    spec = importlib.util.spec_from_file_location("sanitize_profiles", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SanitizeProfilesTests(unittest.TestCase):
    def test_quarantines_invalid_profile_directories(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / ".hermes"
            profiles = home / "profiles"
            (profiles / "coder").mkdir(parents=True)
            bad = profiles / "锟斤拷default"
            bad.mkdir(parents=True)
            (bad / "gateway.pid").write_text("12345\n", encoding="utf-8")

            report = module.sanitize_profiles(home)

            self.assertFalse(bad.exists())
            self.assertEqual(len(report["corrupt_profiles"]), 1)
            quarantine_dir = Path(report["quarantine_dir"])
            self.assertTrue(quarantine_dir.is_dir())
            moved = Path(report["corrupt_profiles"][0]["target"])
            self.assertTrue(moved.is_dir())
            self.assertTrue((moved / "gateway.pid").exists())
            self.assertTrue((quarantine_dir / "manifest.json").exists())
            self.assertTrue((profiles / "coder").exists())

    def test_resets_invalid_active_profile_to_default(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / ".hermes"
            home.mkdir(parents=True)
            (home / "profiles" / "coder").mkdir(parents=True)
            (home / "active_profile").write_text("锟斤拷default\n", encoding="utf-8")

            report = module.sanitize_profiles(home)

            self.assertTrue(report["active_profile_reset"])
            self.assertEqual(report["active_profile_after"], "default")
            self.assertEqual((home / "active_profile").read_text(encoding="utf-8").strip(), "default")

    def test_leaves_valid_profiles_untouched(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / ".hermes"
            profiles = home / "profiles"
            (profiles / "default2").mkdir(parents=True)
            (home / "active_profile").write_text("default\n", encoding="utf-8")

            report = module.sanitize_profiles(home)

            self.assertEqual(report["corrupt_profiles"], [])
            self.assertFalse(report["active_profile_reset"])
            self.assertIsNone(report["quarantine_dir"])
            self.assertTrue((profiles / "default2").exists())


if __name__ == "__main__":
    unittest.main()
