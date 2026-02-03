from typing import Optional, Tuple

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


def generate_text(
    model: str,
    input_text: str,
    instructions: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    previous_response_id: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
) -> Tuple[str, str]:
    if not input_text:
        raise ValueError('Mensagem vazia.')

    settings = get_settings()
    default_temperature = _to_float(settings.get('OPENAI_TEMPERATURE'), 1.0)
    default_max_tokens = _to_int(settings.get('OPENAI_MAX_OUTPUT_TOKENS'), None)

    payload = {
        'model': model,
        'input': input_text,
        'temperature': _to_float(temperature, default_temperature),
    }

    if instructions:
        payload['instructions'] = instructions
    if reasoning_effort:
        payload['reasoning'] = {'effort': reasoning_effort}
    if previous_response_id:
        payload['previous_response_id'] = previous_response_id

    max_tokens = _to_int(max_output_tokens, default_max_tokens)
    if max_tokens is not None and max_tokens > 0:
        payload['max_output_tokens'] = max_tokens

    client = get_openai_client()
    response = client.responses.create(**payload)
    return response.output_text, response.id
