"""Lightweight manual evaluation runner for harness cases."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES_DIR = ROOT / "cases"


def main() -> None:
    print("PPTAgent harness cases")
    print("=" * 40)
    for case_path in sorted(CASES_DIR.glob("*.json")):
        case = json.loads(case_path.read_text(encoding="utf-8"))
        print(f"\n[{case['id']}]")
        print(f"template: {case['template']}")
        print("fields:")
        for key in sorted(case["user_input"].keys()):
            print(f"- {key}")
        print("expectations:")
        for item in case.get("expectations", []):
            print(f"- {item}")


if __name__ == "__main__":
    main()
