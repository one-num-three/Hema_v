from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hermes_cli.profiles import validate_profile_name


def _safe_name(name: str, fallback: str) -> str:
    cleaned = "".join(ch if ch.isascii() and (ch.isalnum() or ch in "-_.") else "_" for ch in name).strip("._")
    return cleaned or fallback


def _is_valid_profile_name(name: str) -> bool:
    try:
        validate_profile_name(name)
        return True
    except ValueError:
        return False


def sanitize_profiles(home: Path) -> dict[str, object]:
    profiles_root = home / "profiles"
    active_profile_file = home / "active_profile"
    quarantine_root = home / "quarantine" / "corrupt_profiles"
    corrupt_dirs = []
    report: dict[str, object] = {
        "home": str(home),
        "profiles_root": str(profiles_root),
        "quarantine_dir": None,
        "corrupt_profiles": [],
        "active_profile_before": "default",
        "active_profile_after": "default",
        "active_profile_reset": False,
    }

    active_before = "default"
    if active_profile_file.exists():
        active_before = active_profile_file.read_text(encoding="utf-8", errors="replace").strip() or "default"
    report["active_profile_before"] = active_before

    if profiles_root.exists():
        for entry in sorted(profiles_root.iterdir(), key=lambda p: p.name):
            if entry.is_dir() and not _is_valid_profile_name(entry.name):
                corrupt_dirs.append(entry)

    quarantine_dir: Path | None = None
    if corrupt_dirs:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quarantine_dir = quarantine_root / stamp
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        report["quarantine_dir"] = str(quarantine_dir)

        for index, source in enumerate(corrupt_dirs, start=1):
            base_name = _safe_name(source.name, f"corrupt_profile_{index}")
            target = quarantine_dir / base_name
            suffix = 1
            while target.exists():
                suffix += 1
                target = quarantine_dir / f"{base_name}_{suffix}"
            shutil.move(str(source), str(target))
            report["corrupt_profiles"].append(
                {
                    "name": source.name,
                    "source": str(source),
                    "target": str(target),
                }
            )

        manifest_path = quarantine_dir / "manifest.json"
        manifest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    active_after = active_before
    if active_before != "default" and not _is_valid_profile_name(active_before):
        active_profile_file.parent.mkdir(parents=True, exist_ok=True)
        active_profile_file.write_text("default\n", encoding="utf-8")
        active_after = "default"
        report["active_profile_reset"] = True

    report["active_profile_after"] = active_after
    return report


def _emit_batch_lines(report: dict[str, object]) -> None:
    corrupt_profiles = report.get("corrupt_profiles", [])
    corrupt_names = [item.get("name", "") for item in corrupt_profiles if isinstance(item, dict)]
    quarantine_dir = report.get("quarantine_dir") or ""
    print(f"CORRUPT_COUNT={len(corrupt_profiles)}")
    print(f"ACTIVE_PROFILE_BEFORE={report.get('active_profile_before', 'default')}")
    print(f"ACTIVE_PROFILE_AFTER={report.get('active_profile_after', 'default')}")
    print(f"ACTIVE_PROFILE_RESET={1 if report.get('active_profile_reset') else 0}")
    print(f"QUARANTINE_DIR={quarantine_dir}")
    print(f"CORRUPT_NAMES_JSON={json.dumps(corrupt_names, ensure_ascii=False)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Quarantine invalid Hermes profile directories.")
    parser.add_argument("--home", type=Path, default=Path.home() / ".hermes", help="Hermes home directory")
    parser.add_argument("--json", action="store_true", help="Emit full JSON report instead of batch lines")
    args = parser.parse_args()

    report = sanitize_profiles(args.home)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _emit_batch_lines(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
