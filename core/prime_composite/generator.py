"""
Random generation of prime and composite questions: STAAR's ways of asking, written or as
multiple choice, and on a self-check tiles sheet, the counting forms whose answers the bank
can't give away.
"""

import random
from collections import defaultdict
from collections.abc import Sequence
from functools import lru_cache
from itertools import product
from math import isqrt

from core.names import NAMES
from core.prime_composite.claims import REASONS, Reason
from core.prime_composite.data import (
    TILE_TYPES,
    ChooseTwoQuestionData,
    Claim,
    CountQuestionData,
    EachNumberQuestionData,
    FactorList,
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
from core.prime_composite.factors import (
    FactorPair,
    Primality,
    factor_pairs,
    factors,
    is_composite,
    is_prime,
    primality,
)
from core.prime_composite.representation import tile_answer
from core.question import FreeResponse, MultipleChoice, Question, multiple_choice

LARGEST_NUMBER = 100  # the default largest number a student judges prime or composite
# A factor-pair question's number is up to this times the largest number: its pairs hold it with
# 1, and its half with 2, so every number a student judges is still at most the largest.
FACTOR_PAIR_REACH = 2
WRONG_OPTIONS = 3  # beside the correct option, in a multiple-choice question
COUNT_LENGTH = 5  # the numbers in a list to count, as STAAR's are
TILE_COUNT_LENGTHS = range(5, 11)  # on a tiles sheet, so 12 different counts are possible
CHOOSE_FROM = 5  # the numbers to choose two from
PEOPLE = 4  # the people whose numbers are given
ROW_LENGTH = 6  # the numbers in a row to mark prime, composite or neither
ROW_PRIMES = (2, 3, 4)  # how many of a row's numbers are prime, each with even chance
ONE_IN_ROW = 1 / 3  # the chance a row has 1 in it, which is neither prime nor composite
MISSING_PRIME_WIDTH = 20  # a list of primes is of those between two multiples of ten this apart
WHOSE_NUMBER_WIDTHS = (10, 20)  # four people's numbers are between multiples of ten this apart
PRIME_COUNT_WIDTHS = range(10, 51, 10)  # on a tiles sheet, to count the primes between
DISTINCT_TRIES = 50  # draws for a question that doesn't repeat one already on the sheet
# largest numbers whose factor-pair shapes and tile candidates are kept, as a sheet asks for
# them once per question, and checking its options asks again
CACHED_LARGEST = 8

# What a tiles sheet's question is made from: its data, or a row's kinds, in order
type TileSeed = (
    FactorPairCountQuestionData | CountQuestionData | PrimeCountQuestionData | tuple[Primality, ...]
)

ASKED = (Primality.PRIME, Primality.COMPOSITE)  # what a question asks for, each with even chance
WORDS = tuple(Primality)  # the words circled under each number: prime, composite, neither
# Which claims are correct for each verdict: the first's and the second's
TRUTHS = {
    Verdict.FIRST: (True, False),
    Verdict.SECOND: (False, True),
    Verdict.BOTH: (True, True),
    Verdict.NEITHER: (False, False),
}


def generate_prime_composite_questions(
    count: int,
    question_types: Sequence[QuestionType],
    *,
    largest_number: int = LARGEST_NUMBER,
    multiple_choice: bool = False,
    distinct_answers: bool = False,
) -> list[PrimeCompositeQuestion]:
    """
    Generate ``count`` questions, shared evenly among ``question_types``, then shuffled. Every
    number a student judges prime or composite is from 1 to ``largest_number``, and no question
    repeats one already on the sheet unless the numbers leave no other.

    Each is written, or with ``multiple_choice``, has lettered choices, as ``_question``
    describes for each type. With ``distinct_answers``, as the self-check tiles case needs, each
    is written in its counting form, as ``_tile_candidates`` describes, and no two answers are
    the same: each question's answer is drawn from those not yet used, with even chance, and a
    type that has run out of answers gives its place to the next type that hasn't.

    Raises ``ValueError`` if ``question_types`` is empty, if both ``multiple_choice`` and
    ``distinct_answers`` are given, if ``distinct_answers`` is given with a type not in
    ``TILE_TYPES``, or if it asks for more questions than ``count_possible_answers`` allows.
    """
    if not question_types:
        raise ValueError("At least one question type is needed.")
    if multiple_choice and distinct_answers:
        raise ValueError("Multiple-choice questions have no answers to keep distinct.")
    types = [question_types[index % len(question_types)] for index in range(count)]
    random.shuffle(types)
    if distinct_answers:
        return _tile_questions(types, question_types, largest_number, count)
    questions: list[PrimeCompositeQuestion] = []
    for question_type in types:
        question = _question(question_type, largest_number, multiple_choice)
        for _ in range(DISTINCT_TRIES):
            if question.data not in (each.data for each in questions):
                break
            question = _question(question_type, largest_number, multiple_choice)
        questions.append(question)
    return questions


def count_possible_answers(question_types: Sequence[QuestionType], largest_number: int) -> int:
    """
    Return how many different answers the tile forms of ``question_types`` can have, at
    ``largest_number``: the most questions ``distinct_answers`` allows. Types not in
    ``TILE_TYPES`` have none.
    """
    return len(
        {
            answer
            for question_type in set(question_types) & set(TILE_TYPES)
            for answer in _tile_candidates(question_type, largest_number)
        }
    )


def _question(question_type: QuestionType, largest: int, choices: bool) -> PrimeCompositeQuestion:
    """Make a question of ``question_type``, with lettered choices if ``choices`` is set."""
    match question_type:
        case QuestionType.FACTOR_PAIRS:
            return _factor_pair_question(largest, choices)
        case QuestionType.COUNT:
            return _count_question(largest, choices)
        case QuestionType.CHOOSE_TWO:
            return _choose_two_question(largest, choices)
        case QuestionType.BETWEEN:
            return _missing_prime_question(largest, choices)
        case QuestionType.WHOSE_NUMBER:
            return _whose_number_question(largest, choices)
        case QuestionType.WHO_IS_CORRECT:
            return _who_is_correct_question(largest, choices)
        case QuestionType.EACH_NUMBER:
            return _each_number_question(largest, choices)
        case QuestionType.LIST_FACTORS:
            return _list_factors_question(largest, choices)


def _factor_pair_question(largest: int, choices: bool) -> PrimeCompositeQuestion:
    """
    Make a question asking for a factor pair with only composite numbers, as STAAR asks it: of a
    number up to ``FACTOR_PAIR_REACH`` times the largest number with such a pair, and at least
    ``WRONG_OPTIONS`` pairs holding 1 or a prime, which are the wrong pairs. One such pair is
    chosen, and the wrong pairs at random.

    With even chance, the plain look asks for a pair of the number, chosen from four with
    ``choices`` or written; the story look has a person list the four pairs, in random order,
    and the student finds the one, chosen in that order or written.

    The numbers alone don't give the answer away:
    - when the pair's numbers are both even, the number's pair with 2 is among the wrong ones,
      so the only pair of even numbers isn't the answer: 2 is even and prime;
    - how many wrong pairs are closer together than the answer, from 0 to 3, is drawn first,
      with even chance among those some number allows, then the number, the pair and the wrong
      pairs that give it. Pairs with only composites are mostly near the middle of a number's
      pairs, so without this the closest pair would most often be the answer.
    """
    shapes = _factor_pair_shapes(largest)
    rank = random.choice(sorted({rank for *_, ranks in shapes for rank in ranks}))
    numbers = sorted({number for number, _, _, _, ranks in shapes if rank in ranks})
    number = random.choice(numbers)
    allowing = {
        pair: (closer, further)
        for n, pair, closer, further, ranks in shapes
        if n == number and rank in ranks
    }
    correct = random.choice(list(allowing))
    closer, further = allowing[correct]
    wrong = random.sample(closer, rank)
    if correct[0] % 2 == 0 and correct[1] % 2 == 0:
        with_two = (2, number // 2)
        rest = [pair for pair in further if pair != with_two]
        wrong += [with_two, *random.sample(rest, WRONG_OPTIONS - rank - 1)]
    else:
        wrong += random.sample(further, WRONG_OPTIONS - rank)
    composite = tuple(pair for pair in factor_pairs(number) if _only_composites(pair))
    if random.choice((False, True)):
        listed = [correct, *wrong]
        random.shuffle(listed)
        data = FactorPairQuestionData(number, composite, random.choice(NAMES), tuple(listed))
        if not choices:
            return Question(data, FreeResponse())
        options = MultipleChoice(tuple(listed), frozenset({listed.index(correct)}))
        return Question(data, options)
    plain = FactorPairQuestionData(number, composite)
    if not choices:
        return Question(plain, FreeResponse())
    return Question(plain, multiple_choice((correct,), tuple(wrong)))


def _count_question(largest: int, choices: bool) -> PrimeCompositeQuestion:
    """
    Make a question asking how many of ``COUNT_LENGTH`` consecutive numbers are prime, or with
    even chance composite. With ``choices``, its options are four consecutive counts from 0 to
    ``COUNT_LENGTH``, the answer among them, each such run with even chance, so the answer is
    not always first, last or between.
    """
    start = random.randint(1, largest - COUNT_LENGTH + 1)
    numbers = tuple(range(start, start + COUNT_LENGTH))
    asked = random.choice(ASKED)
    answer = sum(primality(number) is asked for number in numbers)
    data = CountQuestionData(numbers, asked, answer)
    if not choices:
        return Question(data, FreeResponse())
    first = random.choice(
        [
            low
            for low in range(COUNT_LENGTH - WRONG_OPTIONS + 1)
            if low <= answer <= low + WRONG_OPTIONS
        ]
    )
    counts = range(first, first + WRONG_OPTIONS + 1)
    return Question(data, multiple_choice((answer,), tuple(c for c in counts if c != answer)))


def _choose_two_question(largest: int, choices: bool) -> PrimeCompositeQuestion:
    """
    Make a question asking which two of ``CHOOSE_FROM`` numbers are prime, or with even chance
    composite, the others being 1 and numbers of the other kind. Evenness never picks out the
    answer:
    - composite: at most one of the two is even, so picking the even numbers doesn't find both;
    - prime: the others are odd, or when 2 is one of the two, one of them is even, so 2 isn't
      the only even number.
    """
    numbers = range(1, largest + 1)
    asked = random.choice(ASKED)
    composites = [number for number in numbers if is_composite(number)]
    primes = [number for number in numbers if is_prime(number)]
    if asked is Primality.COMPOSITE:
        correct = random.sample(composites, 2)
        while correct[0] % 2 == 0 and correct[1] % 2 == 0:
            correct = random.sample(composites, 2)
        wrong = random.sample([1, *primes], CHOOSE_FROM - 2)
    else:
        correct = random.sample(primes, 2)
        odd = [1, *(number for number in composites if number % 2)]
        if 2 in correct:
            even = [number for number in composites if number % 2 == 0]
            wrong = [*random.sample(odd, CHOOSE_FROM - 3), random.choice(even)]
        else:
            wrong = random.sample(odd, CHOOSE_FROM - 2)
    shown = tuple(sorted(correct + wrong))
    first, second = sorted(correct)
    data = ChooseTwoQuestionData(shown, asked, (first, second))
    if not choices:
        return Question(data, FreeResponse())
    indexes = frozenset(index for index, number in enumerate(shown) if number in correct)
    return Question(data, MultipleChoice(shown, indexes))


def _missing_prime_question(largest: int, choices: bool) -> PrimeCompositeQuestion:
    """
    Make a question asking for the prime missing from a person's list of the primes between two
    multiples of ten ``MISSING_PRIME_WIDTH`` apart, up to the largest number, with at least
    three primes between them. Any of the primes is the missing one, with even chance.

    With ``choices``, the wrong options are odd numbers between the two that aren't prime, as
    STAAR's are (49, 39 and 33 for the primes between 30 and 50), and ``_ranked_pick`` draws the
    range, the missing prime and them, so the answer is as likely to be the smallest option as
    the largest, or either between. Odd multiples of 5 and 1 are wrong options only when the
    other odd numbers that aren't prime can't give the answer that place.
    """
    ranges = [
        (low, low + MISSING_PRIME_WIDTH)
        for low in range(0, largest - MISSING_PRIME_WIDTH + 1, 10)
        if len(_primes_between(low, low + MISSING_PRIME_WIDTH)) >= 3
    ]
    if not choices:
        low, high = random.choice(ranges)
        answer = random.choice(_primes_between(low, high))
        return Question(
            MissingPrimeQuestionData(random.choice(NAMES), low, high, answer), FreeResponse()
        )
    every: list[tuple[tuple[int, int, int], list[int], list[int]]] = []
    preferred: list[tuple[tuple[int, int, int], list[int], list[int]]] = []
    for low, high in ranges:
        odd = [number for number in range(low + 1, high) if number % 2 and not is_prime(number)]
        for prime in _primes_between(low, high):
            every.append(_around((low, high, prime), prime, odd))
            preferred.append(_around((low, high, prime), prime, [n for n in odd if n % 5]))
    (low, high, answer), wrong = _ranked_pick(every, preferred)
    data = MissingPrimeQuestionData(random.choice(NAMES), low, high, answer)
    return Question(data, multiple_choice((answer,), tuple(wrong)))


def _whose_number_question(largest: int, choices: bool) -> PrimeCompositeQuestion:
    """
    Make a question giving four people's numbers, odd numbers between two multiples of ten, and
    asking whose is prime, or with even chance composite: the others are 1 and numbers of the
    other kind. The numbers are all odd, as STAAR's are, so evenness doesn't pick out the
    answer. ``_ranked_pick`` draws the range and the numbers, so the answer is as likely to be
    the smallest number as the largest, or either between: the multiples of ten are
    ``WHOSE_NUMBER_WIDTHS`` apart, 10, as STAAR's are, when such a range up to the largest
    number can give the answer its place, else 20. No range of 10 has three primes above a
    composite, for one. The names and their order are drawn at random.
    """
    asked = random.choice(ASKED)
    narrow, wide = (
        [
            _around((low, low + width, number), number, pools[1])
            for low in range(0, largest - width + 1, 10)
            if (pools := _whose_number_pools(low, low + width, asked)) is not None
            for number in pools[0]
        ]
        for width in WHOSE_NUMBER_WIDTHS
    )
    (low, high, correct), wrong = _ranked_pick(narrow + wide, narrow)
    numbers = [correct, *wrong]
    random.shuffle(numbers)
    names = random.sample(NAMES, PEOPLE)
    people = tuple(zip(names, numbers, strict=True))
    answer = names[numbers.index(correct)]
    data = WhoseNumberQuestionData(low, high, people, asked, answer)
    if not choices:
        return Question(data, FreeResponse())
    return Question(data, MultipleChoice(tuple(names), frozenset({names.index(answer)})))


def _who_is_correct_question(largest: int, choices: bool) -> PrimeCompositeQuestion:
    """
    Make a question giving two people's claims from ``REASONS``, and asking who is correct, or
    with even chance whose reasoning is correct, which a claim with the right answer for a wrong
    reason needs. The wording is drawn first, then the verdict, each with even chance, so
    neither wording makes any verdict likelier. Then whether both claims are about one number,
    as STAAR's are, or about two, with even chance. Each claim's reason is drawn from those that
    make it correct, or not, as the verdict needs, and that the wording allows, then its number
    from those the reason is about; a second claim about the same number has a reason of its
    own. Claims that can't be made, such as two correct claims about 1, are drawn again.
    """
    numbers = range(1, largest + 1)
    reasoning = random.choice((False, True))
    reasons = [reason for reason in REASONS if reasoning or not reason.flaw]
    while True:
        verdict = random.choice(tuple(Verdict))
        same = random.choice((True, False))
        first_name, second_name = random.sample(NAMES, 2)
        first_truth, second_truth = TRUTHS[verdict]
        first_reason = random.choice(
            [
                reason
                for reason in reasons
                if reason.sound == first_truth and _about(reason, numbers)
            ]
        )
        first_number = random.choice([number for number in numbers if first_reason.about(number)])
        if same:
            second_reasons = [
                reason
                for reason in reasons
                if reason.sound == second_truth
                and reason.text != first_reason.text
                and reason.about(first_number)
            ]
            if not second_reasons:
                continue
            second_reason = random.choice(second_reasons)
            second_number = first_number
        else:
            others = [number for number in numbers if number != first_number]
            second_reason = random.choice(
                [
                    reason
                    for reason in reasons
                    if reason.sound == second_truth and _about(reason, others)
                ]
            )
            second_number = random.choice(
                [number for number in others if second_reason.about(number)]
            )
        break
    claims = (
        _claim(first_name, first_number, first_reason),
        _claim(second_name, second_number, second_reason),
    )
    data = WhoIsCorrectQuestionData(claims, reasoning, verdict)
    if not choices:
        return Question(data, FreeResponse())
    return Question(data, MultipleChoice(tuple(Verdict), frozenset({list(Verdict).index(verdict)})))


def _each_number_question(largest: int, choices: bool) -> PrimeCompositeQuestion:
    """
    Make a row of ``ROW_LENGTH`` numbers to mark prime, composite or neither: ``ROW_PRIMES``
    primes, each count with even chance, and composites, with 1 in place of a composite with
    chance ``ONE_IN_ROW``, in random order. With ``choices``, the three words are circled under
    each number.
    """
    numbers = range(1, largest + 1)
    prime_count = random.choice(ROW_PRIMES)
    row = random.sample([number for number in numbers if is_prime(number)], prime_count)
    row += random.sample(
        [number for number in numbers if is_composite(number)], ROW_LENGTH - prime_count
    )
    if random.random() < ONE_IN_ROW:
        row[-1] = 1
    random.shuffle(row)
    answer = tuple(primality(number) for number in row)
    data = EachNumberQuestionData(tuple(row), answer)
    if not choices:
        return Question(data, FreeResponse())
    return Question(
        data, tuple(MultipleChoice(WORDS, frozenset({WORDS.index(kind)})) for kind in answer)
    )


def _list_factors_question(largest: int, choices: bool) -> PrimeCompositeQuestion:
    """
    Make a question asking for a number's factors, and so whether it is prime or composite: a
    number from 2, or with ``choices`` from 4, to the largest number. 2 and 3 have too few
    believable wrong lists for three wrong options.

    With ``choices``, the wrong options are common mistakes, as ``_wrong_factor_lists`` makes
    them: the right list said to be the other kind, or a factor forgotten or a non-factor added.
    """
    number = random.randint(4 if choices else 2, largest)
    answer: FactorList = (factors(number), primality(number))
    data = ListFactorsQuestionData(number, answer)
    if not choices:
        return Question(data, FreeResponse())
    return Question(data, multiple_choice((answer,), _wrong_factor_lists(number)))


def _wrong_factor_lists(number: int) -> tuple[FactorList, ...]:
    """
    Return three wrong options for a number's factor list, each a mistake:
    - the right list, said to be the other kind;
    - 1 forgotten; for a composite number, the number itself, one factor between them, or every
      one between them (51: 1, 51; prime);
    - a non-factor added, from 2 to one more than the number's square root (51: 1, 3, 7, 17,
      51).
    A list with a mistake in it says what its own factors would make the number, so only the
    first mistake contradicts itself: one factor makes it neither, two prime, more composite.
    How many are longer than the right list, from 0 to 3, is drawn with even chance among the
    counts the mistakes allow, so the right list isn't picked out by its length, nor as the
    shortest or longest list that doesn't contradict itself.
    """
    right = factors(number)
    kind = primality(number)
    other = Primality.PRIME if kind is Primality.COMPOSITE else Primality.COMPOSITE
    same_length: list[FactorList] = [(right, other)]
    forgotten = [right[1:]]
    if kind is Primality.COMPOSITE:
        middle = right[1:-1]
        forgotten += [right[:-1], *(tuple(f for f in right if f != m) for m in middle), (1, number)]
    shorter = [(each, _kind_of(each)) for each in dict.fromkeys(forgotten)]
    longer: list[FactorList] = [
        (tuple(sorted((*right, extra))), Primality.COMPOSITE)
        for extra in range(2, min(number, isqrt(number) + 2))
        if number % extra
    ]
    long_count = random.choice(
        [
            count
            for count in range(WRONG_OPTIONS + 1)
            if count <= len(longer) and WRONG_OPTIONS - count <= len(shorter) + len(same_length)
        ]
    )
    wrong = random.sample(longer, long_count)
    wrong += random.sample(shorter + same_length, WRONG_OPTIONS - long_count)
    return tuple(wrong)


def _tile_questions(
    types: Sequence[QuestionType],
    question_types: Sequence[QuestionType],
    largest: int,
    count: int,
) -> list[PrimeCompositeQuestion]:
    """
    Make the questions of a self-check tiles sheet, of ``types`` in order, as
    ``generate_prime_composite_questions`` describes for ``distinct_answers``. A type with no
    unused answer gives its place to the first of ``question_types`` that has one.

    Raises ``ValueError`` as ``generate_prime_composite_questions`` describes.
    """
    not_tiles = [each for each in question_types if each not in TILE_TYPES]
    if not_tiles:
        listed = ", ".join(each.value for each in not_tiles)
        raise ValueError(f"These question types have no self-check tiles form: {listed}.")
    possible = count_possible_answers(question_types, largest)
    if count > possible:
        raise ValueError(
            f"Cannot make {count} questions with different answers: only {possible} possible."
        )
    candidates = {each: _tile_candidates(each, largest) for each in set(question_types)}
    used: set[str] = set()
    questions: list[PrimeCompositeQuestion] = []
    for question_type in types:
        for each in (question_type, *question_types):
            unused = sorted(set(candidates[each]) - used)
            if unused:
                answer = random.choice(unused)
                questions.append(_tile_question(random.choice(candidates[each][answer]), largest))
                used.add(answer)
                break
    return questions


@lru_cache(maxsize=CACHED_LARGEST)
def _tile_candidates(question_type: QuestionType, largest: int) -> dict[str, list[TileSeed]]:
    """
    Return the questions a self-check tiles sheet can ask of ``question_type``, each as the data
    of its written question, or for a row, the kinds of its numbers, in order, by its answer as
    the bank shows it. Each form's answer isn't printed in the question, so the bank can't give
    it away:
    - factor pairs: how many factor pairs of a composite number up to ``FACTOR_PAIR_REACH``
      times the largest number contain only composite numbers;
    - count: how many of ``TILE_COUNT_LENGTHS`` consecutive numbers are prime, or composite;
    - between: how many primes are between two multiples of ten ``PRIME_COUNT_WIDTHS`` apart;
    - each number: a row of odd numbers above 1 that aren't multiples of 5, but 5, to mark prime
      or composite. 1 is neither, even numbers above 2 are composite and other multiples of 5
      are too: with those, a row's letters could be matched in the bank from them alone.
      ``_tile_question`` draws its numbers.
    Other types have none. Kept for the last few largest numbers, so callers mustn't change
    what it returns.
    """
    found: defaultdict[str, list[TileSeed]] = defaultdict(list)
    match question_type:
        case QuestionType.FACTOR_PAIRS:
            for number in range(4, FACTOR_PAIR_REACH * largest + 1):
                if is_composite(number):
                    pairs = sum(_only_composites(pair) for pair in factor_pairs(number))
                    data = FactorPairCountQuestionData(number, pairs)
                    found[str(pairs)].append(data)
        case QuestionType.COUNT:
            for length in TILE_COUNT_LENGTHS:
                for start in range(1, largest - length + 2):
                    shown = tuple(range(start, start + length))
                    for asked in ASKED:
                        answer = sum(primality(number) is asked for number in shown)
                        found[str(answer)].append(CountQuestionData(shown, asked, answer))
        case QuestionType.BETWEEN:
            for width in PRIME_COUNT_WIDTHS:
                for low in range(0, largest - width + 1, 10):
                    answer = len(_primes_between(low, low + width))
                    found[str(answer)].append(PrimeCountQuestionData(low, low + width, answer))
        case QuestionType.EACH_NUMBER:
            primes, composites = _tile_row_numbers(largest)
            for kinds in product(ASKED, repeat=ROW_LENGTH):
                if kinds.count(Primality.PRIME) <= len(primes) and kinds.count(
                    Primality.COMPOSITE
                ) <= len(composites):
                    found[tile_answer(EachNumberQuestionData((), kinds))].append(kinds)
    return dict(found)


def _tile_question(seed: TileSeed, largest: int) -> PrimeCompositeQuestion:
    """
    Make a tiles sheet's written question from what ``_tile_candidates`` gives: its data, or a
    row's kinds, for which the row's primes, then its composites, are drawn from those
    ``_tile_row_numbers`` gives, and placed in order.
    """
    match seed:
        case FactorPairCountQuestionData():
            return Question(seed, FreeResponse())
        case CountQuestionData():
            return Question(seed, FreeResponse())
        case PrimeCountQuestionData():
            return Question(seed, FreeResponse())
    primes, composites = _tile_row_numbers(largest)
    drawn = {
        Primality.PRIME: iter(random.sample(primes, seed.count(Primality.PRIME))),
        Primality.COMPOSITE: iter(random.sample(composites, seed.count(Primality.COMPOSITE))),
    }
    row = tuple(next(drawn[kind]) for kind in seed)
    return Question(EachNumberQuestionData(row, seed), FreeResponse())


def _tile_row_numbers(largest: int) -> tuple[list[int], list[int]]:
    """
    Return the primes, and the composites, a tiles sheet's row can hold: odd numbers above 1, up
    to ``largest``, that aren't multiples of 5, but 5.
    """
    pool = [number for number in range(3, largest + 1, 2) if number % 5 or number == 5]
    return (
        [number for number in pool if is_prime(number)],
        [number for number in pool if is_composite(number)],
    )


def _factor_pair_numbers(largest: int) -> list[int]:
    """
    Return the numbers a factor-pair question can be about: up to ``FACTOR_PAIR_REACH`` times
    ``largest``, with a factor pair of only composite numbers and ``WRONG_OPTIONS`` pairs that
    hold 1 or a prime.
    """
    return [
        number
        for number in range(4, FACTOR_PAIR_REACH * largest + 1)
        if any(_only_composites(pair) for pair in factor_pairs(number))
        and sum(not _only_composites(pair) for pair in factor_pairs(number)) >= WRONG_OPTIONS
    ]


def _kind_of(listed: tuple[int, ...]) -> Primality:
    """Return what a number would be if ``listed`` were all its factors."""
    if len(listed) == 1:
        return Primality.NEITHER
    return Primality.PRIME if len(listed) == 2 else Primality.COMPOSITE


@lru_cache(maxsize=CACHED_LARGEST)
def _factor_pair_shapes(
    largest: int,
) -> list[tuple[int, FactorPair, list[FactorPair], list[FactorPair], frozenset[int]]]:
    """
    Return every way a factor-pair question can be made from the numbers
    ``_factor_pair_numbers`` gives: each number with a pair of only composites in it, its other
    pairs closer together than that one and further apart, and how many of the closer pairs
    the question can show beside it. When the pair's numbers are both even, the further pairs
    must leave room for the number's pair with 2. Kept for the last few largest numbers, so
    callers mustn't change what it returns.
    """
    shapes = []
    for number in _factor_pair_numbers(largest):
        pairs = factor_pairs(number)
        others = [pair for pair in pairs if not _only_composites(pair)]
        for pair in pairs:
            if not _only_composites(pair):
                continue
            gap = pair[1] - pair[0]
            closer = [other for other in others if other[1] - other[0] < gap]
            further = [other for other in others if other[1] - other[0] > gap]
            least_further = 1 if pair[0] % 2 == 0 and pair[1] % 2 == 0 else 0
            ranks = frozenset(
                rank
                for rank in range(WRONG_OPTIONS + 1)
                if rank <= len(closer) and least_further <= WRONG_OPTIONS - rank <= len(further)
            )
            if ranks:
                shapes.append((number, pair, closer, further, ranks))
    return shapes


def _around[T](made: T, answer: int, wrong: Sequence[int]) -> tuple[T, list[int], list[int]]:
    """Return ``made`` with the numbers of ``wrong`` below ``answer``, and those above it."""
    return (
        made,
        [number for number in wrong if number < answer],
        [number for number in wrong if number > answer],
    )


def _ranked_pick[T](
    candidates: Sequence[tuple[T, list[int], list[int]]],
    preferred: Sequence[tuple[T, list[int], list[int]]] = (),
) -> tuple[T, list[int]]:
    """
    Draw one of ``candidates``, each a question's numbers with the wrong options below its answer
    and above it, and ``WRONG_OPTIONS`` of those wrong options, so that the answer is as likely
    to have any number of them below it as any other some candidate allows: its place among the
    options then doesn't give it away. The count below is drawn first, then a candidate that
    allows it. ``preferred`` holds the same candidates with fewer wrong options, used when one of
    them allows the count.
    """

    def allows(candidate: tuple[T, list[int], list[int]], below: int) -> bool:
        _, under, over = candidate
        return below <= len(under) and WRONG_OPTIONS - below <= len(over)

    counts = sorted(
        {count for count in range(WRONG_OPTIONS + 1) for each in candidates if allows(each, count)}
    )
    count = random.choice(counts)
    pool = [each for each in preferred if allows(each, count)]
    allowing = {
        made: (under, over)
        for made, under, over in pool or candidates
        if allows((made, under, over), count)
    }
    made = random.choice(list(allowing))
    under, over = allowing[made]
    return made, random.sample(under, count) + random.sample(over, WRONG_OPTIONS - count)


def _only_composites(pair: FactorPair) -> bool:
    """Return whether both numbers in a factor pair are composite."""
    return is_composite(pair[0]) and is_composite(pair[1])


def _primes_between(low: int, high: int) -> list[int]:
    """Return the primes between ``low`` and ``high``, not including either, ascending."""
    return [number for number in range(low + 1, high) if is_prime(number)]


def _whose_number_pools(
    low: int, high: int, asked: Primality
) -> tuple[list[int], list[int]] | None:
    """
    Return the odd numbers between ``low`` and ``high`` that are ``asked``, and those that
    aren't, or ``None`` if there are too few for one of the first and three of the others.
    """
    odd = range(low + 1 if low % 2 == 0 else low + 2, high, 2)
    right = [number for number in odd if primality(number) is asked]
    others = [number for number in odd if primality(number) is not asked]
    if not right or len(others) < PEOPLE - 1:
        return None
    return right, others


def _about(reason: Reason, numbers: Sequence[int]) -> bool:
    """Return whether ``reason`` is about any of ``numbers``."""
    return any(reason.about(number) for number in numbers)


def _claim(name: str, number: int, reason: Reason) -> Claim:
    """
    Return ``name``'s claim about ``number`` for ``reason``, with a factor pair of it other
    than 1 and itself drawn at random when the reason has one to fill.
    """
    if "{a}" not in reason.text:
        return Claim(name, number, reason)
    return Claim(name, number, reason, random.choice(factor_pairs(number)[1:]))
