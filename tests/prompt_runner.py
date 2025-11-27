"""Run the prompt_runner against live data and print the LLM reply.

Usage:
    PYTHONPATH=. python tests/prompt_runner.py
Requires:
- config.json for Hyperliquid keys
- OPENAI_API_KEY (or LLM_API_KEY) in env/.env
- network access to api.hyperliquid.xyz and OpenAI
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    try:
        from src.agent.prompt_runner import main as runner_main
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"Failed to import or run prompt runner: {exc}")

    runner_main()


if __name__ == "__main__":
    main()
