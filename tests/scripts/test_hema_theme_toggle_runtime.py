from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "scripts" / "hema_apps_runtime.js"
PATCHER = ROOT / "scripts" / "patch-webui-persistence.py"


def test_hema_runtime_includes_moon_theme_toggle():
    content = RUNTIME.read_text(encoding="utf-8")

    assert "THEME_KEY" in content
    assert "ensureThemeToggle" in content
    assert "hema-theme-toggle" in content
    assert "right:28px" in content
    assert "bottom:128px" in content
    assert "z-index:2147483647" in content
    assert 'root.classList.remove("light")' in content
    assert "html:not(.dark) aside .profile-selector .n-base-selection-label" in content
    assert "html:not(.dark) aside .status-row .n-base-selection-label" in content
    assert 'setAttribute("aria-label", "切换亮色和暗色模式")' in content
    assert "localStorage.setItem(THEME_KEY" in content


def test_hema_runtime_maps_app_background_images():
    content = RUNTIME.read_text(encoding="utf-8")

    assert "background-size:115% auto" in content
    assert ".dark .hema-app-poster:before" in content
    assert ".dark .hema-apps-view" in content
    assert ".dark .hema-app-card" in content

    for name in (
        "ppt.png",
        "nature.png",
        "pdf.png",
        "excel.png",
        "word.png",
        "code.png",
        "plan.png",
        "weekly_report.png",
        "contract.png",
        "learning_ans.png",
        "email.png",
        "more.png",
    ):
        assert f"/hema-app-backgrounds/{name}" in content


def test_hema_apps_patch_version_tracks_theme_toggle():
    content = PATCHER.read_text(encoding="utf-8")

    assert 'HEMA_APPS_SCRIPT_VERSION = "20260529-app-backgrounds-v3"' in content
    assert "HEMA_APPS_ASSET_DIR" in content
    assert "copy2" in content
