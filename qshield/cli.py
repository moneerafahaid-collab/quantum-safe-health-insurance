from __future__ import annotations

import argparse
import json
import sys

import uvicorn

from qshield.config import settings
from qshield.seed import run_console_demo, seed_demo_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Quantum-Safe Health Insurance")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="Run the duplicate-claim console demo")
    sub.add_parser("seed", help="Reset and seed demo claim history")
    serve = sub.add_parser("serve", help="Start the NPHIES middleware API and dashboard")
    serve.add_argument("--host", default=settings.host)
    serve.add_argument("--port", type=int, default=settings.port)

    args = parser.parse_args(argv)
    command = args.command or "serve"
    host = getattr(args, "host", settings.host)
    port = getattr(args, "port", settings.port)

    if command == "demo":
        result = run_console_demo()
        print("=== Quantum-Safe Health Insurance Execution Result ===")
        print(json.dumps(result["decrypted_preview_for_demo"], indent=4, ensure_ascii=False))
        return 0

    if command == "seed":
        seed_demo_data()
        print("Demo history seeded.")
        return 0

    seed_demo_data()
    uvicorn.run("qshield.api:app", host=host, port=port, reload=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
