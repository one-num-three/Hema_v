from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.run import GatewayRunner


def test_create_adapter_returns_weixin_adapter_when_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("WEIXIN_ACCOUNT_ID", "acct")
    monkeypatch.setenv("WEIXIN_TOKEN", "tok")
    runner = GatewayRunner(
        GatewayConfig(
            platforms={
                Platform.WEIXIN: PlatformConfig(
                    enabled=True,
                    token="tok",
                    extra={"account_id": "acct", "base_url": "https://example.invalid"},
                )
            }
        )
    )

    adapter = runner._create_adapter(Platform.WEIXIN, runner.config.platforms[Platform.WEIXIN])

    assert adapter is not None
    assert adapter.platform == Platform.WEIXIN


def test_create_adapter_returns_none_when_weixin_requirements_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delenv("WEIXIN_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("WEIXIN_TOKEN", raising=False)
    runner = GatewayRunner(
        GatewayConfig(
            platforms={
                Platform.WEIXIN: PlatformConfig(enabled=True, token="", extra={})
            }
        )
    )

    adapter = runner._create_adapter(Platform.WEIXIN, runner.config.platforms[Platform.WEIXIN])

    assert adapter is None
