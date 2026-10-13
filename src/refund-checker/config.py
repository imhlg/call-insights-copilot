from pathlib import Path

import anthropic
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")

client = anthropic.Anthropic()
