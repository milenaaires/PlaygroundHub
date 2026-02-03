import sys
import types
import pytest
from pathlib import Path
import importlib.util

class StopApp(Exception): ...
class RerunApp(Exception): ...

class FakeStreamlit:
    def __init__(self, session_state=None):
        self.session_state = session_state or {}
        self.errors = []
        self.successes = []
        self._buttons = {}
        self._text_inputs = {}
        self._selectboxes = {}
        self._checkboxes = {}

    def title(self, *a, **k): pass
    def subheader(self, *a, **k): pass
    def dataframe(self, *a, **k): pass
    def divider(self, *a, **k): pass

    def text_input(self, label, **k):
        return self._text_inputs.get(label, k.get("value", ""))

    def selectbox(self, label, options, **k):
        return self._selectboxes.get(label, options[0])

    def checkbox(self, label, **k):
        return self._checkboxes.get(label, k.get("value", False))

    def button(self, label, **k):
        return self._buttons.get(label, False)

    def success(self, msg): self.successes.append(msg)
    def error(self, msg): self.errors.append(msg)
    def stop(self): raise StopApp()
    def rerun(self): raise RerunApp()

    # st.form suporte
    class _FormCtx:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

    def form(self, *a, **k): return self._FormCtx()
    def form_submit_button(self, *a, **k): return False

def load_page(monkeypatch, page_path: Path, st: FakeStreamlit, *, users, update_called):
    st_mod = types.ModuleType("streamlit")
    for attr in dir(st):
        if not attr.startswith("_"):
            setattr(st_mod, attr, getattr(st, attr))
    st_mod.session_state = st.session_state
    monkeypatch.setitem(sys.modules, "streamlit", st_mod)

    ui_mod = types.ModuleType("src.core.ui")
    ui_mod.sidebar_status = lambda: None
    monkeypatch.setitem(sys.modules, "src.core.ui", ui_mod)

    rbac_mod = types.ModuleType("src.auth.rbac")
    rbac_mod.ROLE_ADMIN = "ADMIN"
    rbac_mod.require_roles = lambda allowed: None
    monkeypatch.setitem(sys.modules, "src.auth.rbac", rbac_mod)

    repo_mod = types.ModuleType("src.repos.users_repo")
    repo_mod.list_users = lambda: users
    repo_mod.create_user = lambda *a, **k: None

    def update_user(*a, **k):
        update_called["called"] = True
    repo_mod.update_user = update_user
    repo_mod.set_password = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "src.repos.users_repo", repo_mod)

    spec = importlib.util.spec_from_file_location("page_admin", page_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

def test_admin_cannot_deactivate_self(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    page = root / "pages" / "2_Admin.py"

    st = FakeStreamlit(session_state={"user_id": 1, "role": "ADMIN"})
    st._text_inputs["Buscar por e-mail"] = ""  # sem filtro
    st._selectboxes["Selecione o ID do usuário"] = 1  # seleciona ele mesmo
    st._checkboxes["Ativo"] = False  # tenta desativar
    st._buttons["Salvar alterações"] = True

    users = [
        {"id": 1, "email": "admin@a.com", "role": "ADMIN", "active": 1},
        {"id": 2, "email": "user@a.com", "role": "USER", "active": 1},
    ]

    update_called = {"called": False}
    load_page(monkeypatch, page, st, users=users, update_called=update_called)

    assert st.errors == ["Você não pode desativar a si mesmo."]
    assert update_called["called"] is False
