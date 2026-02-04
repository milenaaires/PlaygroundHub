from typing import Optional, Dict, Any, Tuple

import re

from src.core.config import get_settings
from src.openai.client import get_openai_client


_COMPLIANCE_SUMMARY_FALLBACK = "(resumo indisponível)"
_COMPLIANCE_SUMMARY_MAX_CHARS = 300


_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_LONG_NUMBER_RE = re.compile(r"\b\d{7,}\b")  # ex.: telefone/conta/IDs longos


def _to_float(value, default: float) -> float:
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default: Optional[int]) -> Optional[int]:
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def upload_pdf(uploaded_file) -> str:
    if uploaded_file is None:
        raise ValueError('Nenhum arquivo enviado.')

    if hasattr(uploaded_file, 'getvalue'):
        file_bytes = uploaded_file.getvalue()
    else:
        file_bytes = uploaded_file.read()

    if not file_bytes:
        raise ValueError('Arquivo vazio.')

    filename = getattr(uploaded_file, 'name', None) or 'documento.pdf'
    content_type = getattr(uploaded_file, 'type', None) or 'application/pdf'

    client = get_openai_client()
    response = client.files.create(
        file=(filename, file_bytes, content_type),
        purpose='user_data',
    )
    return response.id


def _compact_ws(text: str) -> str:
    return " ".join((text or "").split())


def _truncate_text(text: str, max_chars: int) -> str:
    txt = _compact_ws(text)
    if max_chars <= 0 or len(txt) <= max_chars:
        return txt
    if max_chars <= 3:
        return txt[:max_chars]
    return (txt[: max_chars - 3].rstrip() + "...").strip()


def _redact_summary_pii(text: str) -> str:
    # Defesa em profundidade: mesmo com prompt, preferimos não persistir padrões óbvios de PII.
    txt = _EMAIL_RE.sub("[REMOVIDO]", text or "")
    txt = _LONG_NUMBER_RE.sub("[REMOVIDO]", txt)
    return txt


def _clamp_summary(text: str) -> str:
    txt = _compact_ws(text).strip().strip('"').strip("'").strip()
    txt = _redact_summary_pii(txt)
    if not txt:
        return _COMPLIANCE_SUMMARY_FALLBACK
    if len(txt) <= _COMPLIANCE_SUMMARY_MAX_CHARS:
        return txt
    return _truncate_text(txt, _COMPLIANCE_SUMMARY_MAX_CHARS)


def _render_messages_for_compliance_summary(
    messages: list[Dict[str, Any]],
    *,
    max_messages: int = 12,
    per_message_chars: int = 400,
    max_total_chars: int = 4000,
) -> str:
    if not messages:
        return ""

    rendered: list[str] = []
    total = 0
    for msg in messages[-max_messages:]:
        role = str(msg.get("role") or "").strip().upper() or "MESSAGE"
        content = _truncate_text(str(msg.get("content") or ""), per_message_chars)
        if not content:
            continue
        line = f"{role}: {content}".strip()
        if max_total_chars > 0 and total + len(line) > max_total_chars:
            break
        rendered.append(line)
        total += len(line)

    return "\n".join(rendered).strip()


def generate_compliance_summary(messages: list[Dict[str, Any]]) -> str:
    """
    Gera um resumo temático (1–3 frases) para fins de Compliance.

    Importante: este resumo não deve conter PII nem citar trechos verbatim.
    """
    if not messages:
        return "Novo chat iniciado."

    transcript = _render_messages_for_compliance_summary(messages)
    if not transcript:
        return "Novo chat iniciado."

    # Modelo barato/estável (evita depender do modelo configurado no agente).
    model = "gpt-4o-mini"

    instructions = (
        "Você gera um resumo temático para revisão de Compliance.\n"
        "Regras obrigatórias:\n"
        "- 1 a 3 frases, máximo de 300 caracteres.\n"
        "- Não inclua PII (nomes, emails, telefones, endereços, IDs, números de conta etc.).\n"
        "- Não cite/quote mensagens e não copie trechos verbatim.\n"
        "- Descreva apenas o tema e a intenção geral da conversa.\n"
        "- Retorne somente o texto do resumo, sem markdown e sem prefixos."
    )

    try:
        client = get_openai_client()
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=(
                "Resuma o assunto principal desta conversa para Compliance.\n\n"
                f"{transcript}\n"
            ),
            temperature=0.2,
            max_output_tokens=120,
        )
        return _clamp_summary(getattr(response, "output_text", "") or "")
    except Exception:
        return _COMPLIANCE_SUMMARY_FALLBACK


def run_agent_chat(
    agent: Dict[str, Any],
    user_text: str,
    previous_response_id: Optional[str] = None,
    file_id: Optional[str] = None,
) -> Tuple[str, str, Dict[str, Optional[int]]]:
    if not user_text:
        raise ValueError('Mensagem vazia.')

    settings = get_settings()
    default_temperature = _to_float(settings.get('OPENAI_TEMPERATURE'), 1.0)
    default_max_tokens = _to_int(settings.get('OPENAI_MAX_OUTPUT_TOKENS'), None)

    user_content = [{'type': 'input_text', 'text': user_text}]
    if file_id:
        user_content.append({'type': 'input_file', 'file_id': file_id})

    payload = {
        'model': agent['model'],
        'input': [
            {'role': 'user', 'content': user_content},
        ],
        'temperature': _to_float(agent.get('temperature'), default_temperature),
    }

    instructions = (
        agent.get('system_prompt')
        or agent.get('instructions')
        or ''
    )
    if instructions:
        payload['instructions'] = instructions

    reasoning_effort = agent.get('reasoning_effort')
    if reasoning_effort:
        payload['reasoning'] = {'effort': reasoning_effort}
    if previous_response_id:
        payload['previous_response_id'] = previous_response_id

    max_tokens = _to_int(agent.get('max_tokens'), default_max_tokens)
    if max_tokens is not None and max_tokens > 0:
        payload['max_output_tokens'] = max_tokens

    client = get_openai_client()
    response = client.responses.create(**payload)
    usage = {}
    usage_obj = getattr(response, 'usage', None)
    if usage_obj:
        usage = {
            'input_tokens': getattr(usage_obj, 'input_tokens', None),
            'output_tokens': getattr(usage_obj, 'output_tokens', None),
            'total_tokens': getattr(usage_obj, 'total_tokens', None),
        }
    return response.output_text, response.id, usage
