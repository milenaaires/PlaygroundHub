import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / '.env')

from src.openai.text_generation import generate_text


def main():
    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    text, response_id = generate_text(
        model=model,
        input_text='Say this is a test.',
    )
    print('response_id:', response_id)
    print('output_text:', text)


if __name__ == '__main__':
    main()
