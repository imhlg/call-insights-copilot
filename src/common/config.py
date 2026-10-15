from pathlib import Path

import anthropic
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")

client = anthropic.Anthropic()

HK_MODEL = "claude-haiku-5-5"
SONNET_MODEL = "claude-sonnet-5-5"
