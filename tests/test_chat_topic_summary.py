import os
import tempfile

import pytest

from src.core.db import init_db, connect
from src.repos.users_repo import create_user
from src.repos.agents_repo import create_agent
from src.repos.chat_repo import (
    add_message,
    create_chat,
    get_chat,
    update_conversation_topic_summary,
)
from src.agents import service as agents_service


def setup_temp_db():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    os.environ["APP_DB_PATH"] = tmp.name
    init_db()
    return tmp.name


def test_chat_topic_summary_column_and_update():
    setup_temp_db()
    uid = create_user("c@a.com", "pw123456", "USER", True)
    agent_id = create_agent(uid, "Agent A", "Desc A", "gpt-4o-mini", 256, 0.7, "Prompt A")

    chat_id = create_chat(uid, agent_id, title="Chat Teste")
    c1 = get_chat(chat_id, uid)
    assert c1 is not None
    assert c1["conversation_topic_summary"] == "Novo chat iniciado."

    update_conversation_topic_summary(chat_id, uid, "Conversa sobre dúvidas gerais de uso do app.")
    c2 = get_chat(chat_id, uid)
    assert c2 is not None
    assert c2["conversation_topic_summary"] == "Conversa sobre dúvidas gerais de uso do app."


def test_generate_compliance_summary_clamps_length(monkeypatch: pytest.MonkeyPatch):
    long_text = "x" * 10_000

    class _DummyResp:
        output_text = long_text

    class _DummyResponses:
        def create(self, **kwargs):
            return _DummyResp()

    class _DummyClient:
        responses = _DummyResponses()

    monkeypatch.setattr(agents_service, "get_openai_client", lambda: _DummyClient())

    summary = agents_service.generate_compliance_summary(
        [
            {"role": "user", "content": "Como configuro um agente e salvo chats?"},
            {"role": "assistant", "content": "Você pode ajustar modelo, temperatura e prompt."},
        ]
    )
    assert isinstance(summary, str)
    assert 0 < len(summary) <= 300


def test_generate_compliance_summary_fallback_on_client_error(monkeypatch: pytest.MonkeyPatch):
    def _boom():
        raise RuntimeError("no key")

    monkeypatch.setattr(agents_service, "get_openai_client", _boom)

    summary = agents_service.generate_compliance_summary(
        [{"role": "user", "content": "Teste"}]
    )
    assert summary == "(resumo indisponível)"


def test_add_message_persists_attachment_fields():
    setup_temp_db()
    uid = create_user("att@a.com", "pw123456", "USER", True)
    agent_id = create_agent(uid, "Agent A", "Desc A", "gpt-4o-mini", 256, 0.7, "Prompt A")
    chat_id = create_chat(uid, agent_id, title="Chat Attach")

    add_message(
        chat_id,
        "user",
        "Mensagem com anexo",
        tokens=1,
        has_attachment=True,
        attachment_filename=r"C:\\tmp\\meu_pdf.pdf",
    )

    conn = connect()
    try:
        row = conn.execute(
            "SELECT has_attachment, attachment_filename FROM chat_messages WHERE chat_id = ? ORDER BY id DESC LIMIT 1",
            (chat_id,),
        ).fetchone()
        assert row is not None
        assert row["has_attachment"] == 1
        assert row["attachment_filename"] == "meu_pdf.pdf"
    finally:
        conn.close()
