"""The web endpoints serve exactly what the command line makes.

Each snapshot case in ``test_imported_snapshots.CASES`` is requested through the
Django test client, and the PDF must be byte-identical to that case's golden file. The
command line always draws the Name/Date line, so each request asks for it.
"""

import pytest
from django.test import Client

from tests.helpers import GOLDENS


@pytest.mark.parametrize(
    ("pdf_filename", "url"),
    [
        ("block", "/api/worksheets/block.pdf?seed=31&name_line=true"),
        ("strip", "/api/worksheets/strip.pdf?seed=201&name_line=true"),
        ("strip_answer_key", "/api/worksheets/strip.pdf?seed=201&name_line=true&answer_key=true"),
        ("number_line_mc", "/api/worksheets/number_line_mc.pdf?seed=301&name_line=true"),
        ("number_line", "/api/worksheets/number_line.pdf?seed=401&name_line=true"),
        ("multiplication_mc", "/api/worksheets/multiplication_mc.pdf?seed=501&name_line=true"),
        (
            "multiplication_mc_small",
            "/api/worksheets/multiplication_mc.pdf?seed=502&name_line=true&max_factor=10&max_product=50",
        ),
        ("word", "/api/worksheets/word.pdf?seed=601&name_line=true"),
        ("worksheet", "/api/worksheets/worksheet.pdf?seed=701&name_line=true"),
        (
            "worksheet_no_regroup",
            "/api/worksheets/worksheet.pdf?seed=701&name_line=true&no_regroup=true",
        ),
        ("worksheet_bw", "/api/worksheets/worksheet.pdf?seed=702&name_line=true&bw=true"),
        ("data_graph", "/api/worksheets/data_graph.pdf?seed=801&name_line=true"),
        (
            "data_graph_grid",
            "/api/worksheets/data_graph.pdf?seed=802&name_line=true&list_style=grid",
        ),
        (
            "data_graph_commas",
            "/api/worksheets/data_graph.pdf?seed=803&name_line=true&list_style=commas",
        ),
        ("data_graph_mc", "/api/worksheets/data_graph_mc.pdf?seed=901&name_line=true"),
        (
            "data_graph_mc_grid",
            "/api/worksheets/data_graph_mc.pdf?seed=902&name_line=true&list_style=grid",
        ),
    ],
)
def test_pdf_matches_golden(pdf_filename: str, url: str, client: Client) -> None:
    response = client.get(url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content == (GOLDENS / f"{pdf_filename}.pdf").read_bytes()
