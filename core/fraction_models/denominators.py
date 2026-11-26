"""
The denominators a fraction sheet may use, as a teacher types them: numbers and ranges, such as
"2, 3, 4, 6, 8", "2-20" or "10, 100", and what the parts of a whole cut into that many are called.
"""

import re

SMALLEST_DENOMINATOR = 2
LARGEST_DENOMINATOR = 1_000
DEFAULT_DENOMINATORS = "2, 3, 4, 6, 8"  # halves, thirds, fourths, sixths and eighths
DENOMINATORS_HINT = 'Numbers and ranges, such as "2, 3, 4, 6, 8" or "2-12".'

_RANGE = re.compile(r"(\d+)\s*[-\N{EN DASH}]\s*(\d+)")
_GROUPED = re.compile(r"\d,0\d\d\b")  # 1,000: a comma between groups of digits, as no entry
# starts with 0


def parse_denominators(text: str) -> tuple[int, ...]:
    """
    Return the denominators ``text`` lists, ascending, each once: numbers and ranges separated by
    commas, "2-6", with a hyphen or an en dash and spaces or not, meaning 2, 3, 4, 5 and 6.

    Raises ``ValueError``, saying what's wrong, for an empty list, a comma between groups of
    digits ("1,000", since commas separate the entries), an entry that isn't a number or a range,
    a range whose start is above its end, or a number below ``SMALLEST_DENOMINATOR`` or above
    ``LARGEST_DENOMINATOR``.
    """
    found: set[int] = set()
    entries = [entry.strip() for entry in text.split(",")]
    if not any(entries):
        raise ValueError("list at least one denominator, such as 2, 3, 4, 6, 8")
    if match := _GROUPED.search(text):
        raise ValueError(f'"{match[0]}": write numbers without commas, such as 1000')
    for entry in entries:
        if not entry:
            continue  # "2, 3," or "2,, 3"
        if entry.isdigit():
            low = high = int(entry)
        elif match := _RANGE.fullmatch(entry):
            low, high = int(match[1]), int(match[2])
            if low > high:
                raise ValueError(f'"{entry}" runs backwards: write it {high}-{low}')
        else:
            raise ValueError(f'"{entry}" isn\'t a number or a range such as 2-12')
        for value in (low, high):
            if not SMALLEST_DENOMINATOR <= value <= LARGEST_DENOMINATOR:
                raise ValueError(
                    f"{value} is out of range: denominators go from {SMALLEST_DENOMINATOR} to "
                    f"{LARGEST_DENOMINATOR:,}"
                )
        found.update(range(low, high + 1))
    return tuple(sorted(found))


_ONES = ("", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
_TEENS = (
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
# Ordinal words that aren't the number's word with "th" added
_ORDINALS = {
    "one": "first",
    "two": "second",
    "three": "third",
    "five": "fifth",
    "eight": "eighth",
    "nine": "ninth",
    "twelve": "twelfth",
}


def part_name(parts: int) -> str:
    """
    Return what the parts of a whole cut into ``parts`` equal parts are called, as in "sixths are
    larger than eighths": "halves", "thirds", "fourths", "twelfths", "twenty-firsts",
    "hundredths", "one hundred twentieths", "thousandths".

    Raises ``ValueError`` outside ``SMALLEST_DENOMINATOR`` to ``LARGEST_DENOMINATOR``.
    """
    if not SMALLEST_DENOMINATOR <= parts <= LARGEST_DENOMINATOR:
        raise ValueError(
            f"Parts go from {SMALLEST_DENOMINATOR} to {LARGEST_DENOMINATOR:,}, not {parts}."
        )
    if parts == 2:
        return "halves"
    if parts in (100, 1_000):
        return "hundredths" if parts == 100 else "thousandths"
    words = _number_words(parts)
    return f"{' '.join([*words[:-1], _ordinal(words[-1])])}s"


def _number_words(number: int) -> list[str]:
    """Return a number from 1 to 999 in words, the last of them hyphenated: 121 is "one",
    "hundred", "twenty-one"."""
    hundreds, rest = divmod(number, 100)
    words = [_ONES[hundreds], "hundred"] if hundreds else []
    if 10 <= rest < 20:
        words.append(_TEENS[rest - 10])
    elif rest:
        tens, ones = divmod(rest, 10)
        words.append("-".join(filter(None, (_TENS[tens], _ONES[ones]))))
    return words


def _ordinal(word: str) -> str:
    """Return the ordinal of a number word, its last part made ordinal: "twenty-one" is
    "twenty-first", "twenty" "twentieth"."""
    *start, last = word.split("-")
    if last in _ORDINALS:
        last = _ORDINALS[last]
    elif last.endswith("y"):
        last = f"{last[:-1]}ieth"
    else:
        last = f"{last}th"
    return "-".join([*start, last])
