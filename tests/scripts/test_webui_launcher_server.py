from scripts.webui_launcher_server import _int_query_value


def test_int_query_value_accepts_semicolon_gateway_port():
    query = {"targetPort": ["8648;gatewayPort=8642"]}

    assert _int_query_value(query, "targetPort", 1234) == 8648
    assert _int_query_value(query, "gatewayPort", 1234) == 8642


def test_int_query_value_tolerates_legacy_caret_suffix():
    query = {"targetPort": ["8648^"]}

    assert _int_query_value(query, "targetPort", 1234) == 8648
