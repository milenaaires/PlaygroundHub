import sys
import types
from pathlib import Path
import importlib.util


class StopApp(Exception): ...
class RerunApp(Exception): ...


class FakeStreamlit:
    def __init__(self, session_state=None):
        self.session_state = session_state or {}
        self.errors = []
        self.successes = []
        self.infos = []

        self._buttons = {}
        self._text_inputs = {}
        self._selectboxes = {}
        self._checkboxes = {}
        self._form_submits = {}  # label -> bool

    # ---- basic UI no-op ----
    def title(self, *a, **k): pass
    def subheader(self, *a, **k): pass
    def dataframe(self, *a, **k): pass
    def divider(self, *a, **k): pass
    def write(self, *a, **k): pass
    def caption(self, *a, **k): pass
    def markdown(self, *a, **k): pass

    # ---- widgets ----
    def text_input(self, label, **k):
        return self._text_inputs.get(label, k.get("value", ""))

    def selectbox(self, label, options, **k):
        # options pode ser list[str] ou list[int] etc
        return self._selectboxes.get(label, options[0] if options else None)

    def checkbox(self, label, **k):
        return self._checkboxes.get(label, k.get("value", False))

    def button(self, label, **k):
        return self._buttons.get(label, False)

    def success(self, msg): self.successes.append(msg)
    def error(self, msg): self.errors.append(msg)
    def info(self, msg): self.infos.append(msg)

    def stop(self): raise StopApp()
    def rerun(self): raise RerunApp()

    # ---- columns support ----
    class _ColCtx:
        def __init__(self, st): self._st = st
        def __enter__(self): return self._st
        def __exit__(self, exc_type, exc, tb): return False

    def columns(self, spec, **k):
        # spec pode ser int ou list de tamanhos
        n = spec if isinstance(spec, int) else len(spec)
        return [self._ColCtx(self) for _ in range(n)]

    # ---- st.form support ----
    class _FormCtx:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

    def form(self, *a, **k):
        return self._FormCtx()

    def form_submit_button(self, label, **k):
        return self._form_submits.get(label, False)

    # ---- st.dialog support (decorator) ----
    def dialog(self, title):
        def decorator(fn):
            return fn
        return decorator


def load_page(monkeypatch, page_path: Path, st: FakeStreamlit, *, users, update_called):
    # cria um "module streamlit" fake baseado no FakeStreamlit
    st_mod = types.ModuleType("streamlit")
    for attr in dir(st):
        if not attr.startswith("_"):
            setattr(st_mod, attr, getattr(st, attr))
    st_mod.session_state = st.session_state
    monkeypatch.setitem(sys.modules, "streamlit", st_mod)

    # ui mocks
    ui_mod = types.ModuleType("src.core.ui")
    ui_mod.sidebar_status = lambda: None
    ui_mod.page_header = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "src.core.ui", ui_mod)

    # rbac mocks
    rbac_mod = types.ModuleType("src.auth.rbac")
    rbac_mod.ROLE_ADMIN = "ADMIN"
    rbac_mod.require_roles = lambda allowed: None
    monkeypatch.setitem(sys.modules, "src.auth.rbac", rbac_mod)

    # repo mocks
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


def test_admin_cannot_deactivate_self_dialog(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    page = root / "pages" / "2_⚙️_Admin.py"

    st = FakeStreamlit(session_state={"user_id": 1, "role": "ADMIN", "authenticated": True})
    users = [
        {"id": 1, "email": "admin@a.com", "role": "ADMIN", "active": 1},
        {"id": 2, "email": "user@a.com", "role": "USER", "active": 1},
    ]

    # 1) clica no botão que abre o "Editar usuário"
    st._buttons["✏️ Editar usuário"] = True

    # 2) no modal: escolhe ele mesmo
    st._selectboxes["Selecione o usuário"] = "1 — admin@a.com"

    # 3) tenta desativar
    st._checkboxes["Ativo"] = False

    # 4) submete o form
    st._form_submits["Salvar"] = True

    update_called = {"called": False}
    load_page(monkeypatch, page, st, users=users, update_called=update_called)

    assert st.errors == ["Você não pode desativar a si mesmo."]
    assert update_called["called"] is False
