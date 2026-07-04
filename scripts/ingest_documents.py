#!/usr/bin/env python3
"""Manual document ingestion script for NovaTech documentation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.dependencies import get_ingest_use_case


async def main() -> None:
    force = "--force" in sys.argv
    use_case = get_ingest_use_case()
    count = await use_case.execute(force=force)
    print(f"Ingested {count} document chunks")


if __name__ == "__main__":
    asyncio.run(main())
