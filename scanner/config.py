"""Load config.yaml and .env once; import CFG everywhere."""
from __future__ import annotations
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

with open(ROOT / "config.yaml") as f:
    CFG: dict = yaml.safe_load(f)


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)
