"""Seed development configuration only; no empirical observations are created."""

from __future__ import annotations

import os


def main() -> None:
    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL is not configured; no database seed was written.")
        return
    print(
        "TODO: seed development-only pricing configuration once the configuration table is added."
    )


if __name__ == "__main__":
    main()
