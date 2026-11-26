"""Tests for reading the denominators a teacher types, and naming the parts they make."""

import pytest

from core.fraction_models.denominators import parse_denominators, part_name


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2, 3, 4, 6, 8", (2, 3, 4, 6, 8)),
        ("8,6,4,3,2", (2, 3, 4, 6, 8)),  # in order, without spaces
        ("2-6", (2, 3, 4, 5, 6)),
        ("2 - 4, 10", (2, 3, 4, 10)),
        ("2 \N{EN DASH} 4", (2, 3, 4)),
        ("4, 2-5, 4", (2, 3, 4, 5)),  # each once
        ("2, 3,", (2, 3)),  # a comma too many
        ("2,, 3", (2, 3)),
        ("10, 100, 1000", (10, 100, 1000)),
        ("7-7", (7,)),
    ],
)
def test_parse_denominators(text: str, expected: tuple[int, ...]) -> None:
    assert parse_denominators(text) == expected


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "list at least one denominator, such as 2, 3, 4, 6, 8"),
        (" , ", "list at least one denominator, such as 2, 3, 4, 6, 8"),
        ("1,000", '"1,000": write numbers without commas, such as 1000'),
        ("2-", '"2-" isn\'t a number or a range such as 2-12'),
        ("3, x", '"x" isn\'t a number or a range such as 2-12'),
        ("2.5", '"2.5" isn\'t a number or a range such as 2-12'),
        ("9-3", '"9-3" runs backwards: write it 3-9'),
        ("0", "0 is out of range: denominators go from 2 to 1,000"),
        ("1-4", "1 is out of range: denominators go from 2 to 1,000"),
        ("2, 1001", "1001 is out of range: denominators go from 2 to 1,000"),
    ],
)
def test_parse_denominators_errors(text: str, message: str) -> None:
    with pytest.raises(ValueError) as error:
        parse_denominators(text)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("parts", "expected"),
    [
        (2, "halves"),
        (3, "thirds"),  # an ordinal that isn't the word with "th" added
        (4, "fourths"),
        (5, "fifths"),
        (8, "eighths"),
        (9, "ninths"),
        (10, "tenths"),
        (12, "twelfths"),
        (13, "thirteenths"),
        (20, "twentieths"),  # a ten's "y" becomes "ieth"
        (21, "twenty-firsts"),  # the last part of a hyphenated word is made ordinal
        (100, "hundredths"),
        (101, "one hundred firsts"),
        (120, "one hundred twentieths"),
        (999, "nine hundred ninety-ninths"),
        (1_000, "thousandths"),
    ],
)
def test_part_name(parts: int, expected: str) -> None:
    assert part_name(parts) == expected


@pytest.mark.parametrize(
    ("parts", "message"),
    [
        (1, "Parts go from 2 to 1,000, not 1."),
        (1_001, "Parts go from 2 to 1,000, not 1001."),
    ],
)
def test_part_name_errors(parts: int, message: str) -> None:
    with pytest.raises(ValueError) as error:
        part_name(parts)
    assert str(error.value) == message
