"""
Tests for the prime and composite question generator.

``test_questions`` and ``test_tiles_questions`` script ``random``, so each case lists the
questions that must be produced. The names come from ``tests.data``, standing in for the bank,
and these functions are replaced:

- ``random.shuffle`` reverses the list, so the question types are dealt from the last ticked, a
  multiple-choice question's correct option is last and its wrong options in reverse, and a
  story's pairs, four people's numbers and a row's numbers are reversed.
- ``random.choice`` returns the picks listed in the case, in order. For each question:
  - factor pairs: how many wrong pairs are closer together than the answer, the number, the
    pair, then whether it's the story look, then the story's name;
  - count: whether it asks for primes or composites, then with choices, the first count;
  - choose two: whether it asks for primes or composites, then the even composite shown beside
    2;
  - missing prime, written: the range, then the prime; with choices, how many wrong options are
    below it, then the range and the prime as (low, high, prime); then the name;
  - whose number: whether it asks for primes or composites, how many numbers are below the
    answer, then the range and the answer as (low, high, number);
  - who is correct: the wording, then the verdict, whether the claims are about one number, the
    first claim's reason and number, the second's reason, and its number when it's another,
    then any factor pair a reason fills;
  - each number: how many numbers are prime;
  - list factors: with choices, how many wrong lists are longer;
  - a tiles sheet's: the answer, then what the question is made from.
  A pick that is not among its call's items raises ``ValueError``.
- ``random.sample`` returns the samples listed, in order, and ``random.randint`` the numbers
  drawn: the first of a list to count, and the number whose factors are listed.
  ``random.random`` decides whether a row has 1 in it, below a third.

``test_questions_meet_the_rules`` runs the generator for real and checks every question against
the rules it promises.
"""

import pytest

from core.prime_composite.claims import REASONS
from core.prime_composite.data import (
    TILE_TYPES,
    ChooseTwoQuestionData,
    Claim,
    CountQuestionData,
    EachNumberQuestionData,
    FactorPairCountQuestionData,
    FactorPairQuestionData,
    ListFactorsQuestionData,
    MissingPrimeQuestionData,
    PrimeCompositeQuestion,
    PrimeCountQuestionData,
    QuestionType,
    Verdict,
    WhoIsCorrectQuestionData,
    WhoseNumberQuestionData,
)
from core.prime_composite.factors import Primality, factor_pairs, factors, primality
from core.prime_composite.generator import (
    count_possible_answers,
    generate_prime_composite_questions,
)
from core.prime_composite.representation import tile_answer
from core.question import FreeResponse, MultipleChoice, Question
from tests.data import NAMES
from tests.helpers import (
    choice_returns,
    randint_returns,
    random_returns,
    reverse_shuffle,
    sample_returns,
)

PRIME, COMPOSITE, NEITHER = Primality
FIRST, SECOND, BOTH, NEITHER_OF_THEM = Verdict
(
    FACTOR_PAIRS,
    COUNT,
    CHOOSE_TWO,
    BETWEEN,
    WHOSE_NUMBER,
    WHO_IS_CORRECT,
    EACH_NUMBER,
    LIST_FACTORS,
) = QuestionType
WORDS = (PRIME, COMPOSITE, NEITHER)  # circled under each number, in this order

ONLY_TWO = REASONS[1]  # "{n} is prime because it has only two factors"
PRODUCT = REASONS[2]  # "{n} is composite because {a} x {b} = {n}"
ALL_EVEN = REASONS[9]  # "2 is composite because all even numbers are composite"
ODD_PRIME = REASONS[14]  # "{n} is prime because it is odd", about a prime: the wrong reason


@pytest.mark.parametrize(
    (
        "question_types",
        "count",
        "largest_number",
        "multiple_choice",
        "chosen",
        "sampled",
        "drawn",
        "randoms",
        "expected",
    ),
    [
        (
            # STAAR 2026 Q24: (2, 92) is shown beside a pair of even numbers, and only one wrong
            # pair, (8, 23), can be closer together than (4, 46)
            [FACTOR_PAIRS],
            1,
            100,
            True,
            [1, 184, (4, 46), False],
            [[(8, 23)], [(1, 184)]],
            [],
            [],
            [
                Question(
                    FactorPairQuestionData(184, ((4, 46),)),
                    MultipleChoice(((1, 184), (2, 92), (8, 23), (4, 46)), frozenset({3})),
                )
            ],
        ),
        (
            # the story look, written: the person's pairs, in the reversed order, with both
            # pairs of composites in the answer
            [FACTOR_PAIRS],
            1,
            100,
            False,
            [1, 132, (6, 22), True, "Ana"],
            [[(11, 12)], [(3, 44)]],
            [],
            [],
            [
                Question(
                    FactorPairQuestionData(
                        132, ((4, 33), (6, 22)), "Ana", ((3, 44), (2, 66), (11, 12), (6, 22))
                    ),
                    FreeResponse(),
                )
            ],
        ),
        (
            # STAAR 2024 Q13, with the counts 1 to 4 to choose from
            [COUNT],
            1,
            100,
            True,
            [COMPOSITE, 1],
            [],
            [51],
            [],
            [
                Question(
                    CountQuestionData((51, 52, 53, 54, 55), COMPOSITE, 4),
                    MultipleChoice((3, 2, 1, 4), frozenset({3})),
                )
            ],
        ),
        (
            [COUNT],
            1,
            100,
            False,
            [PRIME],
            [],
            [51],
            [],
            [Question(CountQuestionData((51, 52, 53, 54, 55), PRIME, 1), FreeResponse())],
        ),
        (
            # STAAR 2023 Q26's 4 and 22 are both even, so composites are drawn again
            [CHOOSE_TWO],
            1,
            31,
            True,
            [COMPOSITE],
            [[4, 22], [21, 4], [3, 19, 31]],
            [],
            [],
            [
                Question(
                    ChooseTwoQuestionData((3, 4, 19, 21, 31), COMPOSITE, (4, 21)),
                    MultipleChoice((3, 4, 19, 21, 31), frozenset({1, 3})),
                )
            ],
        ),
        (
            # with 2 to choose, an even composite is shown too
            [CHOOSE_TWO],
            1,
            31,
            False,
            [PRIME, 22],
            [[2, 19], [9, 25]],
            [],
            [],
            [Question(ChooseTwoQuestionData((2, 9, 19, 22, 25), PRIME, (2, 19)), FreeResponse())],
        ),
        (
            # STAAR 2021 Q23: 43, with two wrong options below it
            [BETWEEN],
            1,
            50,
            True,
            [2, (30, 50, 43), "Ben"],
            [[39, 33], [49]],
            [],
            [],
            [
                Question(
                    MissingPrimeQuestionData("Ben", 30, 50, 43),
                    MultipleChoice((49, 33, 39, 43), frozenset({3})),
                )
            ],
        ),
        (
            [BETWEEN],
            1,
            50,
            False,
            [(30, 50), 43, "Ben"],
            [],
            [],
            [],
            [Question(MissingPrimeQuestionData("Ben", 30, 50, 43), FreeResponse())],
        ),
        (
            # STAAR 2018 Q15's numbers, two below the prime
            [WHOSE_NUMBER],
            1,
            40,
            True,
            [PRIME, 2, (30, 40, 37)],
            [[35, 33], [39], ["Eve", "Dot", "Cy", "Ben"]],
            [],
            [],
            [
                Question(
                    WhoseNumberQuestionData(
                        30, 40, (("Eve", 39), ("Dot", 33), ("Cy", 35), ("Ben", 37)), PRIME, "Ben"
                    ),
                    MultipleChoice(("Eve", "Dot", "Cy", "Ben"), frozenset({3})),
                )
            ],
        ),
        (
            # STAAR 2017 Q13's claims, about one number
            [WHO_IS_CORRECT],
            1,
            100,
            True,
            [False, FIRST, True, ONLY_TWO, 2, ALL_EVEN],
            [["Ana", "Ben"]],
            [],
            [],
            [
                Question(
                    WhoIsCorrectQuestionData(
                        (Claim("Ana", 2, ONLY_TWO), Claim("Ben", 2, ALL_EVEN)), False, FIRST
                    ),
                    MultipleChoice((FIRST, SECOND, BOTH, NEITHER_OF_THEM), frozenset({0})),
                )
            ],
        ),
        (
            # about two numbers, a right answer for a wrong reason, and a factor pair filled in
            [WHO_IS_CORRECT],
            1,
            100,
            False,
            [True, SECOND, False, ODD_PRIME, 37, PRODUCT, 51, (3, 17)],
            [["Cy", "Dot"]],
            [],
            [],
            [
                Question(
                    WhoIsCorrectQuestionData(
                        (Claim("Cy", 37, ODD_PRIME), Claim("Dot", 51, PRODUCT, (3, 17))),
                        True,
                        SECOND,
                    ),
                    FreeResponse(),
                )
            ],
        ),
        (
            # 1 takes the last composite's place, then the row is reversed; each number's
            # words to circle
            [EACH_NUMBER],
            1,
            20,
            True,
            [2],
            [[2, 17], [9, 15, 4, 20]],
            [],
            [0.2],
            [
                Question(
                    EachNumberQuestionData(
                        (1, 4, 15, 9, 17, 2),
                        (NEITHER, COMPOSITE, COMPOSITE, COMPOSITE, PRIME, PRIME),
                    ),
                    (
                        MultipleChoice(WORDS, frozenset({2})),
                        MultipleChoice(WORDS, frozenset({1})),
                        MultipleChoice(WORDS, frozenset({1})),
                        MultipleChoice(WORDS, frozenset({1})),
                        MultipleChoice(WORDS, frozenset({0})),
                        MultipleChoice(WORDS, frozenset({0})),
                    ),
                )
            ],
        ),
        (
            # no 1
            [EACH_NUMBER],
            1,
            20,
            False,
            [3],
            [[2, 17, 19], [9, 15, 4]],
            [],
            [0.5],
            [
                Question(
                    EachNumberQuestionData(
                        (4, 15, 9, 19, 17, 2),
                        (COMPOSITE, COMPOSITE, COMPOSITE, PRIME, PRIME, PRIME),
                    ),
                    FreeResponse(),
                )
            ],
        ),
        (
            # one wrong list longer, with a non-factor added; one shorter, every factor between
            # 1 and 51 forgotten; and the right list said to be prime
            [LIST_FACTORS],
            1,
            100,
            True,
            [1],
            [[((1, 3, 7, 17, 51), COMPOSITE)], [((1, 51), PRIME), ((1, 3, 17, 51), PRIME)]],
            [51],
            [],
            [
                Question(
                    ListFactorsQuestionData(51, ((1, 3, 17, 51), COMPOSITE)),
                    MultipleChoice(
                        (
                            ((1, 3, 17, 51), PRIME),
                            ((1, 51), PRIME),
                            ((1, 3, 7, 17, 51), COMPOSITE),
                            ((1, 3, 17, 51), COMPOSITE),
                        ),
                        frozenset({3}),
                    ),
                )
            ],
        ),
        (
            # a prime's three wrong lists: 37 alone, which would make it neither, two with a
            # non-factor added, so the right list is neither the shortest nor the longest
            [LIST_FACTORS],
            1,
            100,
            True,
            [2],
            [[((1, 3, 37), COMPOSITE), ((1, 2, 37), COMPOSITE)], [((37,), NEITHER)]],
            [37],
            [],
            [
                Question(
                    ListFactorsQuestionData(37, ((1, 37), PRIME)),
                    MultipleChoice(
                        (
                            ((37,), NEITHER),
                            ((1, 2, 37), COMPOSITE),
                            ((1, 3, 37), COMPOSITE),
                            ((1, 37), PRIME),
                        ),
                        frozenset({3}),
                    ),
                )
            ],
        ),
        (
            # written, the factors listed from 2
            [LIST_FACTORS],
            1,
            100,
            False,
            [],
            [],
            [2],
            [],
            [Question(ListFactorsQuestionData(2, ((1, 2), PRIME)), FreeResponse())],
        ),
        (
            # two types, dealt from the last
            [COUNT, LIST_FACTORS],
            2,
            100,
            False,
            [PRIME],
            [],
            [37, 51],
            [],
            [
                Question(ListFactorsQuestionData(37, ((1, 37), PRIME)), FreeResponse()),
                Question(CountQuestionData((51, 52, 53, 54, 55), PRIME, 1), FreeResponse()),
            ],
        ),
        (
            # a question that repeats one on the sheet is drawn again
            [COUNT],
            2,
            100,
            False,
            [PRIME, PRIME, COMPOSITE],
            [],
            [51, 51, 51],
            [],
            [
                Question(CountQuestionData((51, 52, 53, 54, 55), PRIME, 1), FreeResponse()),
                Question(CountQuestionData((51, 52, 53, 54, 55), COMPOSITE, 4), FreeResponse()),
            ],
        ),
    ],
)
def test_questions(
    monkeypatch: pytest.MonkeyPatch,
    question_types: list[QuestionType],
    count: int,
    largest_number: int,
    multiple_choice: bool,
    chosen: list[object],
    sampled: list[list[object]],
    drawn: list[int],
    randoms: list[float],
    expected: list[PrimeCompositeQuestion],
) -> None:
    monkeypatch.setattr("core.prime_composite.generator.NAMES", NAMES)
    reverse_shuffle(monkeypatch)
    choice_returns(monkeypatch, chosen)
    sample_returns(monkeypatch, sampled)
    randint_returns(monkeypatch, drawn)
    random_returns(monkeypatch, randoms)
    questions = generate_prime_composite_questions(
        count, question_types, largest_number=largest_number, multiple_choice=multiple_choice
    )
    assert questions == expected


@pytest.mark.parametrize(
    ("question_types", "count", "largest_number", "chosen", "sampled", "expected"),
    [
        (
            # a row's primes, then its composite, placed in order; then a count
            [COUNT, EACH_NUMBER],
            2,
            20,
            [
                "PPCPPP",
                (PRIME, PRIME, COMPOSITE, PRIME, PRIME, PRIME),
                "4",
                CountQuestionData((8, 9, 10, 11, 12), COMPOSITE, 4),
            ],
            [[3, 5, 7, 11, 13], [9]],
            [
                Question(
                    EachNumberQuestionData(
                        (3, 5, 9, 7, 11, 13), (PRIME, PRIME, COMPOSITE, PRIME, PRIME, PRIME)
                    ),
                    FreeResponse(),
                ),
                Question(CountQuestionData((8, 9, 10, 11, 12), COMPOSITE, 4), FreeResponse()),
            ],
        ),
        (
            # factor pairs and primes between, counted
            [FACTOR_PAIRS, BETWEEN],
            2,
            100,
            ["5", PrimeCountQuestionData(30, 50, 5), "2", FactorPairCountQuestionData(132, 2)],
            [],
            [
                Question(PrimeCountQuestionData(30, 50, 5), FreeResponse()),
                Question(FactorPairCountQuestionData(132, 2), FreeResponse()),
            ],
        ),
        (
            # at 20, primes between two multiples of ten number 4 or 8: the third count of them
            # gives its place to factor pairs
            [BETWEEN, FACTOR_PAIRS],
            5,
            20,
            [
                "4",
                PrimeCountQuestionData(0, 10, 4),
                "0",
                FactorPairCountQuestionData(4, 0),
                "8",
                PrimeCountQuestionData(0, 20, 8),
                "1",
                FactorPairCountQuestionData(16, 1),
                "2",
                FactorPairCountQuestionData(36, 2),
            ],
            [],
            [
                Question(PrimeCountQuestionData(0, 10, 4), FreeResponse()),
                Question(FactorPairCountQuestionData(4, 0), FreeResponse()),
                Question(PrimeCountQuestionData(0, 20, 8), FreeResponse()),
                Question(FactorPairCountQuestionData(16, 1), FreeResponse()),
                Question(FactorPairCountQuestionData(36, 2), FreeResponse()),
            ],
        ),
    ],
)
def test_tiles_questions(
    monkeypatch: pytest.MonkeyPatch,
    question_types: list[QuestionType],
    count: int,
    largest_number: int,
    chosen: list[object],
    sampled: list[list[int]],
    expected: list[PrimeCompositeQuestion],
) -> None:
    reverse_shuffle(monkeypatch)
    choice_returns(monkeypatch, chosen)
    sample_returns(monkeypatch, sampled)
    questions = generate_prime_composite_questions(
        count, question_types, largest_number=largest_number, distinct_answers=True
    )
    assert questions == expected


@pytest.mark.parametrize("largest_number", [20, 50, 100, 1000])
@pytest.mark.parametrize("multiple_choice", [False, True])
@pytest.mark.parametrize("question_type", list(QuestionType))
def test_questions_meet_the_rules(
    question_type: QuestionType, multiple_choice: bool, largest_number: int
) -> None:
    questions = generate_prime_composite_questions(
        40, [question_type], largest_number=largest_number, multiple_choice=multiple_choice
    )
    broken = [
        (each, rule)
        for each in questions
        for rule in _broken_rules(each, largest_number, multiple_choice)
    ]
    assert broken == []


@pytest.mark.parametrize("largest_number", [20, 100, 1000])
def test_tiles_questions_meet_the_rules(largest_number: int) -> None:
    questions = generate_prime_composite_questions(
        12, TILE_TYPES, largest_number=largest_number, distinct_answers=True
    )
    counting = (
        FactorPairCountQuestionData,
        CountQuestionData,
        PrimeCountQuestionData,
        EachNumberQuestionData,
    )
    answers = [tile_answer(each.data) for each in questions if isinstance(each.data, counting)]
    rows = [each.data for each in questions if isinstance(each.data, EachNumberQuestionData)]
    assert (len(set(answers)), [_easy(row) for row in rows if _easy(row)]) == (12, [])


@pytest.mark.parametrize(
    ("question_types", "count", "largest_number", "multiple_choice", "distinct", "message"),
    [
        ([], 1, 100, False, False, "At least one question type is needed."),
        (
            [COUNT],
            1,
            100,
            True,
            True,
            "Multiple-choice questions have no answers to keep distinct.",
        ),
        (
            [COUNT, WHOSE_NUMBER, WHO_IS_CORRECT],
            1,
            100,
            False,
            True,
            "These question types have no self-check tiles form: whose_number, who_is_correct.",
        ),
        (
            [COUNT],
            8,
            20,
            False,
            True,
            "Cannot make 8 questions with different answers: only 7 possible.",
        ),
    ],
)
def test_generate_prime_composite_questions_errors(
    question_types: list[QuestionType],
    count: int,
    largest_number: int,
    multiple_choice: bool,
    distinct: bool,
    message: str,
) -> None:
    with pytest.raises(ValueError) as error:
        generate_prime_composite_questions(
            count,
            question_types,
            largest_number=largest_number,
            multiple_choice=multiple_choice,
            distinct_answers=distinct,
        )
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("question_types", "largest_number", "expected"),
    [
        # counts 1 to 7
        ([COUNT], 20, 7),
        ([COUNT], 100, 10),
        # 0 to 2 pairs of composites
        ([FACTOR_PAIRS], 20, 3),
        # 4 primes between 0 and 10, or 10 and 20, and 8 between 0 and 20
        ([BETWEEN], 20, 2),
        # rows of 3, 5, 7, 9, 11, 13, 17 and 19: 9 is the only composite, in one place or none
        ([EACH_NUMBER], 20, 7),
        # counts 0 to 8, and the rows
        (TILE_TYPES, 20, 16),
        (TILE_TYPES, 100, 79),
        # no tiles form
        ([WHOSE_NUMBER], 100, 0),
    ],
)
def test_count_possible_answers(
    question_types: list[QuestionType], largest_number: int, expected: int
) -> None:
    assert count_possible_answers(question_types, largest_number) == expected


def _easy(row: EachNumberQuestionData) -> list[int]:
    """Return a tiles row's numbers whose letters need no judging: 1, even, or ending in 5."""
    return [
        number
        for number in row.numbers
        if number == 1 or number % 2 == 0 or (number % 5 == 0 and number != 5)
    ]


def _broken_rules(each: PrimeCompositeQuestion, largest: int, multiple_choice: bool) -> list[str]:
    """Return the rules ``each`` breaks, of those its type promises, with ``largest``."""
    data, response = each.data, each.response
    broken = []
    choosing = isinstance(response, MultipleChoice)
    if choosing != (multiple_choice and not isinstance(data, EachNumberQuestionData)):
        broken.append("response")
    if choosing:
        assert isinstance(response, MultipleChoice)
        if len(set(response.options)) != len(response.options):
            broken.append("options repeat")
    match data:
        case FactorPairQuestionData():
            pairs = factor_pairs(data.number)
            if data.number > 2 * largest or data.answer != tuple(
                pair for pair in pairs if all(primality(n) is COMPOSITE for n in pair)
            ):
                broken.append("number or answer")
            shown = response.options if isinstance(response, MultipleChoice) else data.listed
            right = [pair for pair in shown if pair in data.answer]
            if shown and (len(right) != 1 or len(shown) != 4 or not set(shown) <= set(pairs)):
                broken.append("pairs shown")
            if (
                shown
                and right[0][0] % 2 == 0
                and right[0][1] % 2 == 0
                and (2, data.number // 2) not in shown
            ):
                broken.append("no pair with 2 beside a pair of even numbers")
        case CountQuestionData():
            if len(data.numbers) != 5 or max(data.numbers) > largest:
                broken.append("numbers")
            if data.answer != sum(primality(n) is data.asked for n in data.numbers):
                broken.append("answer")
            if isinstance(response, MultipleChoice) and (
                sorted(response.options)
                != list(range(min(response.options), min(response.options) + 4))
                or max(response.options) > 5
            ):
                broken.append("counts")
        case ChooseTwoQuestionData():
            right = [n for n in data.numbers if primality(n) is data.asked]
            if tuple(right) != data.answer or max(data.numbers) > largest:
                broken.append("answer or numbers")
            if data.asked is COMPOSITE and all(n % 2 == 0 for n in right):
                broken.append("both composites even")
            others = [n for n in data.numbers if n not in right]
            if data.asked is PRIME and any(n % 2 == 0 for n in others) != (2 in right):
                broken.append("evens beside the primes")
        case MissingPrimeQuestionData():
            between = [n for n in range(data.low + 1, data.high) if primality(n) is PRIME]
            if sorted((*data.listed, data.answer)) != between or data.high > largest:
                broken.append("list")
            if isinstance(response, MultipleChoice) and any(
                n % 2 == 0 or primality(n) is PRIME or not data.low < n < data.high
                for n in response.options
                if n != data.answer
            ):
                broken.append("wrong options")
        case WhoseNumberQuestionData():
            numbers = [number for _, number in data.people]
            asked = [name for name, number in data.people if primality(number) is data.asked]
            if (
                asked != [data.answer]
                or any(n % 2 == 0 or not data.low < n < data.high for n in numbers)
                or data.high > largest
            ):
                broken.append("numbers")
        case WhoIsCorrectQuestionData():
            first, second = (claim.reason.sound for claim in data.claims)
            verdict = {(True, False): FIRST, (False, True): SECOND, (True, True): BOTH}.get(
                (first, second), NEITHER_OF_THEM
            )
            flawed = any(claim.reason.flaw for claim in data.claims)
            if verdict is not data.answer or (flawed and not data.reasoning):
                broken.append("verdict or wording")
            if any(
                not claim.reason.about(claim.number) or claim.number > largest
                for claim in data.claims
            ):
                broken.append("numbers")
        case EachNumberQuestionData():
            if (
                data.answer != tuple(primality(n) for n in data.numbers)
                or max(data.numbers) > largest
            ):
                broken.append("answer or numbers")
        case ListFactorsQuestionData():
            if (
                data.answer != (factors(data.number), primality(data.number))
                or data.number > largest
            ):
                broken.append("answer or number")
    return broken
