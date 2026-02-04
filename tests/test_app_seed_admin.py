import sys
import types
from pathlib import Path
import importlib.util

class FakeCtx:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

def test_seed_admin_creates_user_when_missing(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    app_path = root / "app.py"

    # streamlit stub
    st_mod = types.ModuleType("streamlit")
    st_mod.set_page_config = lambda **k: None
    st_mod.columns = lambda *a, **k: (FakeCtx(), FakeCtx())
    st_mod.image = lambda *a, **k: None
    st_mod.markdown = lambda *a, **k: None
    st_mod.caption = lambda *a, **k: None
    st_mod.divider = lambda *a, **k: None
    st_mod.write = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "streamlit", st_mod)

    db_mod = types.ModuleType("src.core.db")
    db_mod.init_db = lambda: None
    monkeypatch.setitem(sys.modules, "src.core.db", db_mod)

    cfg_mod = types.ModuleType("src.core.config")
    cfg_mod.get_settings = lambda: {"ADMIN_EMAIL": "ADMIN@EMPRESA.COM", "ADMIN_PASSWORD": "SenhaForte123"}
    monkeypatch.setitem(sys.modules, "src.core.config", cfg_mod)

    ui_mod = types.ModuleType("src.core.ui")
    ui_mod.sidebar_status = lambda: None
    ui_mod.page_header = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "src.core.ui", ui_mod)

    calls = {"created": None}

    repo_mod = types.ModuleType("src.repos.users_repo")
    repo_mod.get_user_by_email = lambda email: None  # não existe ainda
    def create_user(**kwargs):
        calls["created"] = kwargs
    repo_mod.create_user = create_user
    monkeypatch.setitem(sys.modules, "src.repos.users_repo", repo_mod)

    spec = importlib.util.spec_from_file_location("app_main", app_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    assert calls["created"] is not None
    assert calls["created"]["email"] == "admin@empresa.com"
    assert calls["created"]["role"] == "ADMIN"
    assert calls["created"]["active"] is True
