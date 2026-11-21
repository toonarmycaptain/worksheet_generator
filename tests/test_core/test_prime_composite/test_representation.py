"""
Tests for what a prime and composite question shows: its question, its options, the answer
key's entry and its self-check tiles form.

The questions are built by hand, most from STAAR's released items. Claims take their reasons
from ``REASONS`` by position; new reasons go at its end, so these stay the same.
"""

import pytest

from core.prime_composite.claims import REASONS
from core.prime_composite.data import (
    ChooseTwoQuestionData,
    Claim,
    CountQuestionData,
    EachNumberQuestionData,
    FactorPairCountQuestionData,
    FactorPairQuestionData,
    ListFactorsQuestionData,
    MissingPrimeQuestionData,
    PrimeCountQuestionData,
    Verdict,
    WhoIsCorrectQuestionData,
    WhoseNumberQuestionData,
)
from core.prime_composite.factors import Primality
from core.prime_composite.representation import (
    PrimeCompositeQuestionData,
    TileQuestionData,
    factor_list_text,
    pair_text,
    prime_composite_tile_question,
    question,
    solution,
    verdict_text,
)
from core.self_check_tiles import TileQuestion

PRIME, COMPOSITE, NEITHER = Primality
FIRST, SECOND, BOTH, NEITHER_OF_THEM = Verdict

ONLY_TWO = REASONS[1]  # "{n} is prime because it has only two factors"
PRODUCT = REASONS[2]  # "{n} is composite because {a} x {b} = {n}"
ALL_EVEN = REASONS[9]  # "2 is composite because all even numbers are composite"
ONE_PRIME = REASONS[11]  # "1 is prime because it has only one factor"
ONE_COMPOSITE = REASONS[12]  # "1 is composite because it is a factor of every number"
ODD_PRIME = REASONS[14]  # "{n} is prime because it is odd", about a prime: the wrong reason

# STAAR 2017 Q13
BRENDA_AND_CARLA = WhoIsCorrectQuestionData(
    (Claim("Brenda", 2, ONLY_TWO), Claim("Carla", 2, ALL_EVEN)), False, FIRST
)
# a right answer for a wrong reason, about two numbers
CY_AND_DOT = WhoIsCorrectQuestionData(
    (Claim("Cy", 37, ODD_PRIME), Claim("Dot", 51, PRODUCT, (3, 17))), True, SECOND
)
SETH = FactorPairQuestionData(
    132, ((4, 33), (6, 22)), "Seth", ((6, 22), (11, 12), (3, 44), (2, 66))
)
# STAAR 2018 Q15
STUDENTS = WhoseNumberQuestionData(
    30, 40, (("Elly", 35), ("Ulysses", 39), ("Maggie", 37), ("Palmer", 33)), PRIME, "Maggie"
)
ROW = EachNumberQuestionData(
    (1, 9, 17, 21, 2, 57), (NEITHER, COMPOSITE, PRIME, COMPOSITE, PRIME, COMPOSITE)
)


@pytest.mark.parametrize(
    ("data", "choices", "expected"),
    [
        (
            FactorPairQuestionData(184, ((4, 46),)),
            True,
            "Which factor pair of 184 contains only composite numbers?",
        ),
        (
            FactorPairQuestionData(184, ((4, 46),)),
            False,
            "Write a factor pair of 184 that contains only composite numbers.",
        ),
        (
            # the story look: written the same way either way
            SETH,
            True,
            "Seth wrote four factor pairs for 132: 6 \N{MULTIPLICATION SIGN} 22, "
            "11 \N{MULTIPLICATION SIGN} 12, 3 \N{MULTIPLICATION SIGN} 44, "
            "2 \N{MULTIPLICATION SIGN} 66. Which of Seth's factor pairs contains only composite "
            "numbers?",
        ),
        (
            SETH,
            False,
            "Seth wrote four factor pairs for 132: 6 \N{MULTIPLICATION SIGN} 22, "
            "11 \N{MULTIPLICATION SIGN} 12, 3 \N{MULTIPLICATION SIGN} 44, "
            "2 \N{MULTIPLICATION SIGN} 66. Which of Seth's factor pairs contains only composite "
            "numbers?",
        ),
        (
            FactorPairCountQuestionData(132, 2),
            False,
            "How many factor pairs of 132 contain only composite numbers?",
        ),
        (
            CountQuestionData((51, 52, 53, 54, 55), COMPOSITE, 4),
            True,
            "A list of numbers is shown: 51, 52, 53, 54, 55. How many numbers in the list are "
            "composite numbers?",
        ),
        (
            CountQuestionData((51, 52, 53, 54, 55), PRIME, 1),
            False,
            "A list of numbers is shown: 51, 52, 53, 54, 55. How many numbers in the list are "
            "prime numbers?",
        ),
        (
            ChooseTwoQuestionData((3, 4, 19, 22, 31), COMPOSITE, (4, 22)),
            True,
            "Which of these are composite numbers? Select TWO correct answers.",
        ),
        (
            ChooseTwoQuestionData((3, 4, 19, 22, 31), COMPOSITE, (4, 22)),
            False,
            "Circle the two composite numbers.",
        ),
        (
            MissingPrimeQuestionData("Jaylen", 30, 50, 43),
            True,
            "Jaylen was told to list all the prime numbers between 30 and 50: 31, 37, 41, 47. "
            "Which prime number is missing from Jaylen's list?",
        ),
        (
            PrimeCountQuestionData(30, 50, 5),
            False,
            "How many prime numbers are there between 30 and 50?",
        ),
        (
            STUDENTS,
            True,
            "Four students each wrote down a number between 30 and 40. Elly wrote 35, Ulysses "
            "wrote 39, Maggie wrote 37 and Palmer wrote 33. Which student wrote down a prime "
            "number?",
        ),
        (
            BRENDA_AND_CARLA,
            True,
            "Brenda said that 2 is prime because it has only two factors. Carla said that 2 is "
            "composite because all even numbers are composite. Who is correct?",
        ),
        (
            BRENDA_AND_CARLA,
            False,
            "Brenda said that 2 is prime because it has only two factors. Carla said that 2 is "
            "composite because all even numbers are composite. Who is correct? Explain how you "
            "know.",
        ),
        (
            CY_AND_DOT,
            True,
            "Cy said that 37 is prime because it is odd. Dot said that 51 is composite because "
            "3 \N{MULTIPLICATION SIGN} 17 = 51. Whose reasoning is correct?",
        ),
        (ROW, True, "Circle prime, composite or neither under each number."),
        (
            ROW,
            False,
            "Write P under each prime number, C under each composite number and N under each "
            "number that is neither.",
        ),
        (
            ListFactorsQuestionData(51, ((1, 3, 17, 51), COMPOSITE)),
            True,
            "Which shows all the factors of 51, and whether 51 is prime or composite?",
        ),
        (
            ListFactorsQuestionData(51, ((1, 3, 17, 51), COMPOSITE)),
            False,
            "List all the factors of 51. Is 51 prime or composite?",
        ),
    ],
)
def test_question(data: PrimeCompositeQuestionData, choices: bool, expected: str) -> None:
    assert question(data, choices) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # the plain look writes a pair larger first, as STAAR's do
        (FactorPairQuestionData(184, ((4, 46),)), "46 and 4"),
        # written, every pair with only composites
        (FactorPairQuestionData(132, ((4, 33), (6, 22))), "33 and 4, or 22 and 6"),
        # the story look: the one listed
        (SETH, "6 \N{MULTIPLICATION SIGN} 22"),
        (
            FactorPairCountQuestionData(132, 2),
            "2: 4 \N{MULTIPLICATION SIGN} 33 and 6 \N{MULTIPLICATION SIGN} 22",
        ),
        (FactorPairCountQuestionData(46, 0), "0"),
        (CountQuestionData((51, 52, 53, 54, 55), COMPOSITE, 4), "4: 51, 52, 54 and 55"),
        (CountQuestionData((90, 91, 92, 93, 94), PRIME, 0), "0"),
        (ChooseTwoQuestionData((3, 4, 19, 22, 31), COMPOSITE, (4, 22)), "4 and 22"),
        (MissingPrimeQuestionData("Jaylen", 30, 50, 43), "43"),
        (PrimeCountQuestionData(30, 50, 5), "5: 31, 37, 41, 43, 47"),
        (
            STUDENTS,
            "Maggie. 35 = 5 \N{MULTIPLICATION SIGN} 7; 39 = 3 \N{MULTIPLICATION SIGN} 13; 37 is "
            "prime; 33 = 3 \N{MULTIPLICATION SIGN} 11.",
        ),
        (
            WhoseNumberQuestionData(
                0, 10, (("Ana", 1), ("Ben", 9), ("Cy", 3), ("Dot", 7)), COMPOSITE, "Ben"
            ),
            "Ben. 1 is neither prime nor composite; 9 = 3 \N{MULTIPLICATION SIGN} 3; 3 is prime; "
            "7 is prime.",
        ),
        (BRENDA_AND_CARLA, "Brenda is correct. 2 is prime: its only factors are 1 and 2."),
        (
            # the wrong reason's flaw, with a counterexample
            CY_AND_DOT,
            "Dot's reasoning is correct. 37 is prime: its only factors are 1 and 37. 51 is "
            "composite: 3 \N{MULTIPLICATION SIGN} 17 = 51. Being odd doesn't make a number "
            "prime: 9 is odd and composite.",
        ),
        (
            WhoIsCorrectQuestionData(
                (Claim("Ana", 1, ONE_PRIME), Claim("Ben", 1, ONE_COMPOSITE)), False, NEITHER_OF_THEM
            ),
            "Neither of them is correct. 1 is neither prime nor composite: its only factor is 1.",
        ),
        (ROW, "1: N, 9: C, 17: P, 21: C, 2: P, 57: C"),
        (ListFactorsQuestionData(51, ((1, 3, 17, 51), COMPOSITE)), "1, 3, 17, 51; composite"),
    ],
)
def test_solution(data: PrimeCompositeQuestionData, expected: str) -> None:
    assert solution(data) == expected


@pytest.mark.parametrize(
    ("data", "verdict", "expected"),
    [
        (BRENDA_AND_CARLA, FIRST, "Brenda is correct."),
        (BRENDA_AND_CARLA, SECOND, "Carla is correct."),
        (BRENDA_AND_CARLA, BOTH, "Both of them are correct."),
        (BRENDA_AND_CARLA, NEITHER_OF_THEM, "Neither of them is correct."),
        (CY_AND_DOT, FIRST, "Cy's reasoning is correct."),
        (CY_AND_DOT, SECOND, "Dot's reasoning is correct."),
        (CY_AND_DOT, BOTH, "Both students' reasoning is correct."),
        (CY_AND_DOT, NEITHER_OF_THEM, "Neither student's reasoning is correct."),
    ],
)
def test_verdict_text(data: WhoIsCorrectQuestionData, verdict: Verdict, expected: str) -> None:
    assert verdict_text(data, verdict) == expected


@pytest.mark.parametrize(
    ("data", "pair", "expected"),
    [
        (FactorPairQuestionData(184, ((4, 46),)), (8, 23), "23 and 8"),
        (SETH, (11, 12), "11 \N{MULTIPLICATION SIGN} 12"),
    ],
)
def test_pair_text(data: FactorPairQuestionData, pair: tuple[int, int], expected: str) -> None:
    assert pair_text(data, pair) == expected


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        (((1, 51), PRIME), "1, 51; prime"),
        (((29,), NEITHER), "29; neither"),
    ],
)
def test_factor_list_text(option: tuple[tuple[int, ...], Primality], expected: str) -> None:
    assert factor_list_text(option) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            FactorPairCountQuestionData(132, 2),
            TileQuestion(
                prompt="How many factor pairs of 132 contain only composite numbers?",
                answer="2",
                solution="2: 4 \N{MULTIPLICATION SIGN} 33 and 6 \N{MULTIPLICATION SIGN} 22",
            ),
        ),
        (
            CountQuestionData((70, 71, 72, 73, 74, 75, 76, 77), PRIME, 2),
            TileQuestion(
                prompt="A list of numbers is shown: 70, 71, 72, 73, 74, 75, 76, 77. How many "
                "numbers in the list are prime numbers?",
                answer="2",
                solution="2: 71 and 73",
            ),
        ),
        (
            PrimeCountQuestionData(40, 50, 3),
            TileQuestion(
                prompt="How many prime numbers are there between 40 and 50?",
                answer="3",
                solution="3: 41, 43, 47",
            ),
        ),
        (
            # a row's letters, with no spaces, so they fit a bank box on one line
            EachNumberQuestionData(
                (21, 31, 87, 29, 73, 41), (COMPOSITE, PRIME, COMPOSITE, PRIME, PRIME, PRIME)
            ),
            TileQuestion(
                prompt="Write P under each prime number, C under each composite number and N "
                "under each number that is neither.",
                answer="CPCPPP",
                solution="21: C, 31: P, 87: C, 29: P, 73: P, 41: P",
            ),
        ),
    ],
)
def test_prime_composite_tile_question(data: TileQuestionData, expected: TileQuestion) -> None:
    assert prime_composite_tile_question(data) == expected
