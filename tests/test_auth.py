from src.auth import hash_password, verify_password

def test_hash_and_verify():
    pw = "SenhaForte@123"
    h = hash_password(pw)
    assert h != pw
    assert verify_password(pw, h) is True
    assert verify_password("errada", h) is False
