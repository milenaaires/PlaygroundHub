from typing import Optional, Dict, Any, Tuple

from src.core.config import get_settings
from src.openai.client import get_openai_client


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
