"""RASHKAR canonical reference datasets."""

from pathlib import Path

RASHKAR_DATA_DIR = Path(__file__).resolve().parent
MAHARASHTRA_APY_CANONICAL_CSV = RASHKAR_DATA_DIR / "maharashtra_apy_canonical.csv"

__all__ = ["RASHKAR_DATA_DIR", "MAHARASHTRA_APY_CANONICAL_CSV"]
