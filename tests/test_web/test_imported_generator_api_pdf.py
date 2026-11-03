"""The web endpoints serve exactly what the command line makes.

Each snapshot case in ``test_imported_snapshots.CASES`` is requested through the
Django test client, and the PDF must be byte-identical to that case's golden file.
"""

import pytest
from django.test import Client

from tests.test_imported_snapshots import GOLDENS


@pytest.mark.parametrize(
    ("pdf_filename", "url"),
    [
        ("block", "/api/worksheets/block.pdf?seed=31"),
        ("strip", "/api/worksheets/strip.pdf?seed=201"),
        ("strip_answer_key", "/api/worksheets/strip.pdf?seed=201&answer_key=true"),
        ("number_line_mc", "/api/worksheets/number_line_mc.pdf?seed=301"),
        ("number_line", "/api/worksheets/number_line.pdf?seed=401"),
        ("multiplication_mc", "/api/worksheets/multiplication_mc.pdf?seed=501"),
        (
            "multiplication_mc_small",
            "/api/worksheets/multiplication_mc.pdf?seed=502&max_factor=10&max_product=50",
        ),
        ("word", "/api/worksheets/word.pdf?seed=601"),
        ("worksheet", "/api/worksheets/worksheet.pdf?seed=701"),
        ("worksheet_no_regroup", "/api/worksheets/worksheet.pdf?seed=701&no_regroup=true"),
        ("worksheet_bw", "/api/worksheets/worksheet.pdf?seed=702&bw=true"),
        ("data_graph", "/api/worksheets/data_graph.pdf?seed=801"),
        ("data_graph_grid", "/api/worksheets/data_graph.pdf?seed=802&list_style=grid"),
        ("data_graph_commas", "/api/worksheets/data_graph.pdf?seed=803&list_style=commas"),
        ("data_graph_mc", "/api/worksheets/data_graph_mc.pdf?seed=901"),
        ("data_graph_mc_grid", "/api/worksheets/data_graph_mc.pdf?seed=902&list_style=grid"),
    ],
)
def test_pdf_matches_golden(pdf_filename: str, url: str, client: Client) -> None:
    response = client.get(url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content == (GOLDENS / f"{pdf_filename}.pdf").read_bytes()
