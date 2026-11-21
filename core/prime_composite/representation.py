"""
What a prime and composite question shows: its question, the wording of its options, the
answer key's entry, and on a self-check tiles sheet, the answer as the bank shows it.
"""

from collections.abc import Iterable, Sequence

from core.prime_composite.data import (
    ChooseTwoQuestionData,
    Claim,
    CountQuestionData,
    EachNumberQuestionData,
    FactorList,
    FactorPairCountQuestionData,
    FactorPairQuestionData,
    ListFactorsQuestionData,
    MissingPrimeQuestionData,
    PrimeCountQuestionData,
    QuestionType,
    Verdict,
    WhoIsCorrectQuestionData,
    WhoseNumberQuestionData,
)
from core.prime_composite.factors import (
    FactorPair,
    Primality,
    factor_pairs,
    is_composite,
    is_prime,
    primality,
)
from core.self_check_tiles import TileQuestion

PRIME_COMPOSITE_NAME = "Prime and Composite Numbers"
QUESTION_TYPE_NAMES = {
    QuestionType.FACTOR_PAIRS: "Factor pairs with only composite numbers",
    QuestionType.COUNT: "Count the primes or composites in a list",
    QuestionType.CHOOSE_TWO: "Choose the two primes or composites",
    QuestionType.BETWEEN: "Primes between two numbers",
    QuestionType.WHOSE_NUMBER: "Whose number is prime or composite",
    QuestionType.WHO_IS_CORRECT: "Who is correct?",
    QuestionType.EACH_NUMBER: "Prime, composite or neither for each number",
    QuestionType.LIST_FACTORS: "List the factors, then decide",
}
LETTERS = {Primality.PRIME: "P", Primality.COMPOSITE: "C", Primality.NEITHER: "N"}
EXPLAIN = "Explain how you know."  # after a written "Who is correct?"

# Any question's data that has a question of its own, as each type's data is
type PrimeCompositeQuestionData = (
    FactorPairQuestionData
    | FactorPairCountQuestionData
    | CountQuestionData
    | ChooseTwoQuestionData
    | MissingPrimeQuestionData
    | PrimeCountQuestionData
    | WhoseNumberQuestionData
    | WhoIsCorrectQuestionData
    | EachNumberQuestionData
    | ListFactorsQuestionData
)
# The data of the counting forms a self-check tiles sheet asks
type TileQuestionData = (
    FactorPairCountQuestionData
    | CountQuestionData
    | PrimeCountQuestionData
    | EachNumberQuestionData
)


def question(data: PrimeCompositeQuestionData, choices: bool) -> str:
    """
    Return the question, as STAAR words it where it asks it, worded for lettered choices with
    ``choices``, else for a written answer. Numbers to choose from or mark, such as a row's, are
    drawn below it, not written in it.
    """
    match data:
        case FactorPairQuestionData():
            if data.name is not None:
                listed = ", ".join(pair_text(data, pair) for pair in data.listed)
                return (
                    f"{data.name} wrote four factor pairs for {data.number}: {listed}. Which of "
                    f"{_possessive(data.name)} factor pairs contains only composite numbers?"
                )
            if choices:
                return f"Which factor pair of {data.number} contains only composite numbers?"
            return f"Write a factor pair of {data.number} that contains only composite numbers."
        case FactorPairCountQuestionData():
            return f"How many factor pairs of {data.number} contain only composite numbers?"
        case CountQuestionData():
            return (
                f"A list of numbers is shown: {', '.join(map(str, data.numbers))}. How many "
                f"numbers in the list are {data.asked} numbers?"
            )
        case ChooseTwoQuestionData():
            if choices:
                return f"Which of these are {data.asked} numbers? Select TWO correct answers."
            return f"Circle the two {data.asked} numbers."
        case MissingPrimeQuestionData():
            return (
                f"{data.name} was told to list all the prime numbers between {data.low} and "
                f"{data.high}: {', '.join(map(str, data.listed))}. Which prime number is "
                f"missing from {_possessive(data.name)} list?"
            )
        case PrimeCountQuestionData():
            return f"How many prime numbers are there between {data.low} and {data.high}?"
        case WhoseNumberQuestionData():
            people = _listed(f"{name} wrote {number}" for name, number in data.people)
            return (
                f"Four students each wrote down a number between {data.low} and {data.high}. "
                f"{people}. Which student wrote down a {data.asked} number?"
            )
        case WhoIsCorrectQuestionData():
            said = " ".join(f"{claim.name} said that {claim_text(claim)}." for claim in data.claims)
            asked = "Whose reasoning is correct?" if data.reasoning else "Who is correct?"
            return f"{said} {asked}" if choices else f"{said} {asked} {EXPLAIN}"
        case EachNumberQuestionData():
            if choices:
                return "Circle prime, composite or neither under each number."
            return (
                "Write P under each prime number, C under each composite number and N under "
                "each number that is neither."
            )
        case ListFactorsQuestionData():
            if choices:
                return (
                    f"Which shows all the factors of {data.number}, and whether {data.number} "
                    "is prime or composite?"
                )
            return f"List all the factors of {data.number}. Is {data.number} prime or composite?"


def pair_text(data: FactorPairQuestionData, pair: FactorPair) -> str:
    """
    Return a factor pair as the question's look writes it, as STAAR's do: "6 x 22", smaller
    first, in the story look, and "46 and 4", larger first, in the plain one.
    """
    small, large = pair
    return f"{small} \N{MULTIPLICATION SIGN} {large}" if data.name else f"{large} and {small}"


def claim_text(claim: Claim) -> str:
    """Return a claim with its number, and any factor pair, filled in."""
    a, b = claim.pair or (0, 0)
    return claim.reason.text.format(n=claim.number, a=a, b=b)


def verdict_text(data: WhoIsCorrectQuestionData, verdict: Verdict) -> str:
    """
    Return the option for ``verdict``, as STAAR words it ("Brenda is correct."), or when the
    question asks whose reasoning is correct, worded for that.
    """
    first, second = (claim.name for claim in data.claims)
    if data.reasoning:
        return {
            Verdict.FIRST: f"{_possessive(first)} reasoning is correct.",
            Verdict.SECOND: f"{_possessive(second)} reasoning is correct.",
            Verdict.BOTH: "Both students' reasoning is correct.",
            Verdict.NEITHER: "Neither student's reasoning is correct.",
        }[verdict]
    return {
        Verdict.FIRST: f"{first} is correct.",
        Verdict.SECOND: f"{second} is correct.",
        Verdict.BOTH: "Both of them are correct.",
        Verdict.NEITHER: "Neither of them is correct.",
    }[verdict]


def factor_list_text(option: FactorList) -> str:
    """Return a number's factors and what they make it: "1, 3, 17, 51; composite"."""
    listed, kind = option
    return f"{', '.join(map(str, listed))}; {kind}"


def fact(number: int) -> str:
    """
    Return what a number is and why, as an answer key gives it: "37 is prime: its only factors
    are 1 and 37", "51 is composite: 3 x 17 = 51", or for 1, that it is neither.
    """
    if number == 1:
        return "1 is neither prime nor composite: its only factor is 1"
    if is_prime(number):
        return f"{number} is prime: its only factors are 1 and {number}"
    small, large = factor_pairs(number)[1]
    return f"{number} is composite: {small} \N{MULTIPLICATION SIGN} {large} = {number}"


def solution(data: PrimeCompositeQuestionData) -> str:
    """
    Return the answer key's entry, after the correct letters for lettered choices: the answer,
    with the numbers or facts that show it where they help.
    """
    match data:
        case FactorPairQuestionData():
            shown = [pair for pair in data.answer if pair in data.listed] or data.answer
            return ", or ".join(pair_text(data, pair) for pair in shown)
        case FactorPairCountQuestionData():
            pairs = [
                f"{a} \N{MULTIPLICATION SIGN} {b}"
                for a, b in factor_pairs(data.number)
                if _composites(a, b)
            ]
            return f"{data.answer}: {_listed(pairs)}" if pairs else "0"
        case CountQuestionData():
            found = [number for number in data.numbers if primality(number) is data.asked]
            return f"{data.answer}: {_listed(map(str, found))}" if found else "0"
        case ChooseTwoQuestionData():
            return _listed(map(str, data.answer))
        case MissingPrimeQuestionData():
            return str(data.answer)
        case PrimeCountQuestionData():
            primes = [n for n in range(data.low + 1, data.high) if is_prime(n)]
            return f"{data.answer}: {', '.join(map(str, primes))}" if primes else "0"
        case WhoseNumberQuestionData():
            return f"{data.answer}. {'; '.join(_short_fact(n) for _, n in data.people)}."
        case WhoIsCorrectQuestionData():
            numbers = dict.fromkeys(claim.number for claim in data.claims)
            facts = " ".join(f"{fact(number)}." for number in numbers)
            flaws = [
                claim.reason.flaw
                for claim in data.claims
                if claim.reason.flaw and claim.reason.says is primality(claim.number)
            ]
            return " ".join([verdict_text(data, data.answer), facts, *dict.fromkeys(flaws)])
        case EachNumberQuestionData():
            return ", ".join(
                f"{number}: {LETTERS[kind]}"
                for number, kind in zip(data.numbers, data.answer, strict=True)
            )
        case ListFactorsQuestionData():
            return factor_list_text(data.answer)


def tile_answer(data: TileQuestionData) -> str:
    """
    Return the answer as the self-check tiles bank shows it: a count, or a row's letters, as in
    "CPCPCP".
    """
    if isinstance(data, EachNumberQuestionData):
        return "".join(LETTERS[kind] for kind in data.answer)
    return str(data.answer)


def prime_composite_tile_question(data: TileQuestionData) -> TileQuestion:
    """
    Convert a counting form's data to a ``TileQuestion``: the prompt is the question, the answer
    as the bank shows it, and the solution the answer key's entry.
    """
    return TileQuestion(
        prompt=question(data, choices=False), answer=tile_answer(data), solution=solution(data)
    )


def numbers_shown(data: PrimeCompositeQuestionData) -> Sequence[int]:
    """
    Return the numbers drawn below the question, to circle or mark: a row's, or the numbers to
    choose two from when written. None for the other questions.
    """
    if isinstance(data, (EachNumberQuestionData, ChooseTwoQuestionData)):
        return data.numbers
    return ()


def _short_fact(number: int) -> str:
    """Return what a number is, briefly: "37 is prime", "35 = 5 x 7", "1 is neither"."""
    if number == 1:
        return "1 is neither prime nor composite"
    if is_prime(number):
        return f"{number} is prime"
    small, large = factor_pairs(number)[1]
    return f"{number} = {small} \N{MULTIPLICATION SIGN} {large}"


def _composites(first: int, second: int) -> bool:
    """Return whether both numbers are composite."""
    return is_composite(first) and is_composite(second)


def _listed(items: Iterable[str]) -> str:
    """Return items as a list in a sentence: "A", "A and B", "A, B and C"."""
    names = list(items)
    return " and ".join(filter(None, (", ".join(names[:-1]), names[-1]))) if names else ""


def _possessive(name: str) -> str:
    """Return a name's possessive: "Seth's", and "Ulysses's", as Chicago style has it."""
    return f"{name}'s"
