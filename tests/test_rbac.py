from src.auth.rbac import is_allowed

def test_is_allowed():
    assert is_allowed("ADMIN", {"ADMIN"}) is True
    assert is_allowed("USER", {"ADMIN"}) is False
    assert is_allowed(None, {"ADMIN"}) is False
