from gateway.config import Platform, load_gateway_config


def test_load_gateway_config_enables_weixin_from_env(monkeypatch):
    monkeypatch.setenv("WEIXIN_ACCOUNT_ID", "bot-account")
    monkeypatch.setenv("WEIXIN_TOKEN", "bot-token")
    monkeypatch.setenv("WEIXIN_BASE_URL", "https://example.invalid")

    config = load_gateway_config()

    assert Platform.WEIXIN in config.platforms
    weixin = config.platforms[Platform.WEIXIN]
    assert weixin.enabled is True
    assert weixin.token == "bot-token"
    assert weixin.extra["account_id"] == "bot-account"
    assert weixin.extra["base_url"] == "https://example.invalid"


def test_load_gateway_config_skips_weixin_without_required_token(monkeypatch):
    monkeypatch.delenv("WEIXIN_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("WEIXIN_TOKEN", raising=False)
    monkeypatch.delenv("WEIXIN_BASE_URL", raising=False)
    monkeypatch.setenv("WEIXIN_ACCOUNT_ID", "bot-account")

    config = load_gateway_config()

    assert Platform.WEIXIN not in config.platforms
