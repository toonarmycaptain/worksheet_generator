"""
Data for prime and composite questions: STAAR's ways of asking which numbers are prime or
composite, and counting versions of them whose answers a self-check tiles bank can't give away.
"""

from dataclasses import dataclass
from enum import StrEnum

from core.prime_composite.claims import Reason
from core.prime_composite.factors import FactorPair, Primality, primality
from core.question import FreeResponse, MultipleChoice, Question, QuestionData

# A number's factors, ascending, and what they make it: ((1, 3, 17, 51), Primality.COMPOSITE)
type FactorList = tuple[tuple[int, ...], Primality]


class QuestionType(StrEnum):
    """
    A kind of question on a prime and composite sheet. Each is asked written or as multiple
    choice, and some in a counting form on a self-check tiles sheet. Values are stable
    identifiers for the API and storage.
    """

    FACTOR_PAIRS = "factor_pairs"  # a factor pair with only composite numbers
    COUNT = "count"  # how many numbers in a list are prime, or composite
    CHOOSE_TWO = "choose_two"  # the two primes, or composites, among five numbers
    BETWEEN = "between"  # the prime missing from a list of those between two numbers
    WHOSE_NUMBER = "whose_number"  # which of four people's numbers is prime, or composite
    WHO_IS_CORRECT = "who_is_correct"  # which of two people's claims are correct
    EACH_NUMBER = "each_number"  # whether each number in a row is prime, composite or neither
    LIST_FACTORS = "list_factors"  # a number's factors, and so whether it is prime or composite


# The types a self-check tiles sheet asks, in forms whose answer the question doesn't show
TILE_TYPES = (
    QuestionType.FACTOR_PAIRS,
    QuestionType.COUNT,
    QuestionType.BETWEEN,
    QuestionType.EACH_NUMBER,
)


class Verdict(StrEnum):
    """Which of two people's claims are correct. Values are stable identifiers."""

    FIRST = "first"
    SECOND = "second"
    BOTH = "both"
    NEITHER = "neither"


@dataclass(frozen=True)
class FactorPairQuestionData(QuestionData[tuple[FactorPair, ...]]):
    """
    Asks for a factor pair of ``number`` with only composite numbers in it; ``answer`` holds
    every such pair, in the order of ``factor_pairs``.

    In the story look, a person, ``name``, has written the factor pairs in ``listed``, exactly
    one of them in ``answer``, and the student finds that one. Otherwise ``name`` is ``None``,
    ``listed`` is empty, and the pairs to choose from, if any, are the response's.
    """

    number: int
    answer: tuple[FactorPair, ...]
    name: str | None = None
    listed: tuple[FactorPair, ...] = ()


@dataclass(frozen=True)
class FactorPairCountQuestionData(QuestionData[int]):
    """Asks how many factor pairs of ``number`` contain only composite numbers: ``answer``."""

    number: int
    answer: int


@dataclass(frozen=True)
class CountQuestionData(QuestionData[int]):
    """
    Asks how many of ``numbers``, consecutive and ascending, are ``asked``, prime or composite:
    ``answer``.
    """

    numbers: tuple[int, ...]
    asked: Primality
    answer: int


@dataclass(frozen=True)
class ChooseTwoQuestionData(QuestionData[tuple[int, int]]):
    """
    Asks which two of ``numbers``, ascending, are ``asked``, prime or composite: ``answer``, in
    ascending order. A multiple-choice question's options are ``numbers``, in that order.
    """

    numbers: tuple[int, ...]
    asked: Primality
    answer: tuple[int, int]


@dataclass(frozen=True)
class MissingPrimeQuestionData(QuestionData[int]):
    """
    A person, ``name``, has listed the primes between ``low`` and ``high`` but one, ``answer``,
    which the student finds.
    """

    name: str
    low: int
    high: int
    answer: int

    @property
    def listed(self) -> tuple[int, ...]:
        """The primes listed, in ascending order: those between the bounds but the answer."""
        return tuple(
            number
            for number in range(self.low + 1, self.high)
            if number != self.answer and primality(number) is Primality.PRIME
        )


@dataclass(frozen=True)
class PrimeCountQuestionData(QuestionData[int]):
    """Asks how many primes are between ``low`` and ``high``: ``answer``."""

    low: int
    high: int
    answer: int


@dataclass(frozen=True)
class WhoseNumberQuestionData(QuestionData[str]):
    """
    Four people each wrote down a number between ``low`` and ``high``, as (name, number) in
    ``people``, and exactly one of the numbers is ``asked``, prime or composite: the student
    finds whose, ``answer``. A multiple-choice question's options are the names, in that order.
    """

    low: int
    high: int
    people: tuple[tuple[str, int], ...]
    asked: Primality
    answer: str


@dataclass(frozen=True)
class Claim:
    """
    A person, ``name``, claims ``number`` is prime, composite or neither, for ``reason``.
    ``pair`` fills the reason's ``{a}`` and ``{b}``, and is ``None`` when it has none.
    """

    name: str
    number: int
    reason: Reason
    pair: FactorPair | None = None


@dataclass(frozen=True)
class WhoIsCorrectQuestionData(QuestionData[Verdict]):
    """
    Two people's ``claims``, and which are correct, ``answer``. A claim is correct only when its
    answer and its reason are both right. With ``reasoning``, the question asks whose reasoning
    is correct, as it must when a claim has the right answer for a wrong reason. A
    multiple-choice question's options are every ``Verdict``, in order.
    """

    claims: tuple[Claim, Claim]
    reasoning: bool
    answer: Verdict


@dataclass(frozen=True)
class EachNumberQuestionData(QuestionData[tuple[Primality, ...]]):
    """Asks whether each of ``numbers`` is prime, composite or neither: ``answer``, in order."""

    numbers: tuple[int, ...]
    answer: tuple[Primality, ...]


@dataclass(frozen=True)
class ListFactorsQuestionData(QuestionData[FactorList]):
    """Asks for the factors of ``number``, and so whether it is prime or composite: ``answer``."""

    number: int
    answer: FactorList


# Each kind of question as presented. A factor pair's options are pairs, written as the data's
# look writes them; a row of numbers, as multiple choice, has the three words to circle under
# each number, each a choice of its own.
type FactorPairQuestion = Question[
    FactorPairQuestionData, FreeResponse | MultipleChoice[FactorPair]
]
type CountQuestion = Question[CountQuestionData, FreeResponse | MultipleChoice[int]]
type ChooseTwoQuestion = Question[ChooseTwoQuestionData, FreeResponse | MultipleChoice[int]]
type MissingPrimeQuestion = Question[MissingPrimeQuestionData, FreeResponse | MultipleChoice[int]]
type WhoseNumberQuestion = Question[WhoseNumberQuestionData, FreeResponse | MultipleChoice[str]]
type WhoIsCorrectQuestion = Question[
    WhoIsCorrectQuestionData, FreeResponse | MultipleChoice[Verdict]
]
type EachNumberQuestion = Question[
    EachNumberQuestionData, FreeResponse | tuple[MultipleChoice[Primality], ...]
]
type ListFactorsQuestion = Question[
    ListFactorsQuestionData, FreeResponse | MultipleChoice[FactorList]
]
# The counting forms a self-check tiles sheet asks, always written
type FactorPairCountQuestion = Question[FactorPairCountQuestionData, FreeResponse]
type PrimeCountQuestion = Question[PrimeCountQuestionData, FreeResponse]

# Any question on a prime and composite sheet
type PrimeCompositeQuestion = (
    FactorPairQuestion
    | CountQuestion
    | ChooseTwoQuestion
    | MissingPrimeQuestion
    | WhoseNumberQuestion
    | WhoIsCorrectQuestion
    | EachNumberQuestion
    | ListFactorsQuestion
    | FactorPairCountQuestion
    | PrimeCountQuestion
)
