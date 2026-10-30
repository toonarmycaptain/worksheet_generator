"""Byte-stable snapshot (golden) tests for the imported TEKS worksheet scripts.

Every imported ``generate_*`` script must produce byte-identical PDF output for a
fixed seed, so later refactors can be shown not to change existing worksheets.

reportlab is made deterministic with ``rl_config.invariant`` (a fixed timestamp and
document id), set in ``conftest.py``.  Each case drives the script's own ``main()``
through argv, so the snapshot is exactly what the command line produces.

Regenerate the golden files after an intended change::

    REGEN_GOLDENS=1 uv run pytest tests/test_imported_snapshots.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

GOLDENS = Path(__file__).parent / "goldens"
_PKG = "worksheet_generator._imported."

# case id -> (script module, seed, extra CLI args).  --seed and --out are added below.
CASES: dict[str, tuple[str, int, list[str]]] = {
    "block": ("generate_block_word_problems", 31, []),
    "strip": ("generate_strip_word_problems", 201, []),
    "strip_answer_key": ("generate_strip_word_problems", 201, ["--answer-key"]),
    "number_line_mc": ("generate_number_line_mc_word_problems", 301, []),
    "number_line": ("generate_number_line_word_problems", 401, []),
    "multiplication_mc": ("generate_multiplication_mc_word_problems", 501, []),
    "multiplication_mc_small": (
        "generate_multiplication_mc_word_problems",
        502,
        ["--max-factor", "10", "--max-product", "50"],
    ),
    "word": ("generate_word_problems", 601, []),
    "worksheet": ("generate_worksheet", 701, []),
    "worksheet_no_regroup": ("generate_worksheet", 701, ["--no-regroup"]),
    "worksheet_bw": ("generate_worksheet", 702, ["--bw"]),
    "data_graph": ("generate_data_graph_word_problems", 801, []),
    "data_graph_grid": ("generate_data_graph_word_problems", 802, ["--list-style", "grid"]),
    "data_graph_commas": ("generate_data_graph_word_problems", 803, ["--list-style", "commas"]),
    "data_graph_mc": ("generate_data_graph_mc_word_problems", 901, []),
    "data_graph_mc_grid": ("generate_data_graph_mc_word_problems", 902, ["--list-style", "grid"]),
}


def _render(case_id: str, out_dir: Path, monkeypatch: pytest.MonkeyPatch) -> bytes:
    module_name, seed, extra = CASES[case_id]
    module = importlib.import_module(_PKG + module_name)
    out = out_dir / f"{case_id}.pdf"
    monkeypatch.setattr(sys, "argv", [module_name, "--seed", str(seed), "--out", str(out), *extra])
    module.main()
    return out.read_bytes()


@pytest.mark.parametrize("case_id", list(CASES))
def test_snapshot(case_id: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    actual = _render(case_id, tmp_path, monkeypatch)
    golden = GOLDENS / f"{case_id}.pdf"

    # Uncomment to regenerate:
    # GOLDENS.mkdir(exist_ok=True)
    # golden.write_bytes(actual)

    assert golden.exists(), f"missing {golden.name}"
    assert actual == golden.read_bytes(), (
        f"{case_id} output changed ({len(actual)} bytes, golden {golden.stat().st_size})"
    )
