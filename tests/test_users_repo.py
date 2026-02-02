import os
import tempfile
from src.core.db import init_db
from src.repos.users_repo import create_user, get_user_by_email, list_users, update_user, set_password
from src.auth.auth import verify_password

def setup_temp_db():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    os.environ["APP_DB_PATH"] = tmp.name
    init_db()
    return tmp.name

def test_create_and_get_user():
    setup_temp_db()
    uid = create_user("test@a.com", "abc12345", "USER", active=True)
    u = get_user_by_email("test@a.com")
    assert u["id"] == uid
    assert u["role"] == "USER"
    assert u["active"] == 1

def test_update_user_role_and_active():
    setup_temp_db()
    uid = create_user("x@a.com", "abc12345", "USER", active=True)
    update_user(uid, role="COMPLIANCE", active=False)
    u = get_user_by_email("x@a.com")
    assert u["role"] == "COMPLIANCE"
    assert u["active"] == 0

def test_set_password_changes_hash():
    setup_temp_db()
    uid = create_user("p@a.com", "oldpass123", "USER", active=True)
    u1 = get_user_by_email("p@a.com")
    assert verify_password("oldpass123", u1["password_hash"]) is True

    set_password(uid, "newpass123")
    u2 = get_user_by_email("p@a.com")
    assert verify_password("newpass123", u2["password_hash"]) is True
    assert verify_password("oldpass123", u2["password_hash"]) is False

def test_list_users():
    setup_temp_db()
    create_user("a@a.com", "pw123456", "USER", True)
    create_user("b@a.com", "pw123456", "ADMIN", True)
    users = list_users()
    assert len(users) >= 2
