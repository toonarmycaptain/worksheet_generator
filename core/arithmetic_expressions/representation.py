"""
Writing an arithmetic expression, inline and as pieces for a PDF to draw, and reading one from
text.

Signs have a space each side, 28 + 7 x (12 - 4), with the minus sign rather than a hyphen. A group
is written with the symbols it stores, as STAAR writes them, ( ) inside [ ]; with ``brackets``
off, every group is written in parentheses: 8 + ((9 - 5) x (3 + 7)) - 2. Groups nest at most two
deep, the TEKS's "up to two levels of grouping".

An expression is written only if the text reads back as the same tree by the order of operations:
20 - 5 + 3 is ``(20 - 5) + 3``, and ``20 - (5 + 3)`` has to be grouped to be written. A
multiplication written without its sign joins its two sides as one, as a fraction bar would, so it
is worked before a x or ÷ beside it: 60 ÷ 6[2 + 8] is 60 over 6[2 + 8], 60 ÷ 60 = 1.
"""

import re
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from typing import TypeIs, assert_never

from core.arithmetic_expressions.data import (
    Calculation,
    Expression,
    Grouping,
    Number,
    NumberValue,
    Variable,
)
from core.basic_operations.data import Operation
from core.basic_operations.representation import SYMBOLS
from core.written_numbers import (
    MINUS,
    NumberStyle,
    Piece,
    Pieces,
    inline,
    merge_pieces,
    number_pieces,
)

# Multiplication and division are worked before addition and subtraction, and a multiplication
# written without its sign before them
_PRECEDENCE = {
    Operation.ADD: 1,
    Operation.SUBTRACT: 1,
    Operation.MULTIPLY: 2,
    Operation.DIVIDE: 2,
}
_IMPLIED_PRECEDENCE = 3
_OPEN = {Grouping.PARENTHESES: "(", Grouping.BRACKETS: "["}
_CLOSE = {Grouping.PARENTHESES: ")", Grouping.BRACKETS: "]"}
_CENT = Decimal("0.01")

# What ``parse`` reads: a mixed number, a fraction, a number with commas and a decimal point, a
# letter, or a sign or grouping symbol (a hyphen for minus and * for times as well)
_TOKEN = re.compile(
    r"\s*(?:(?P<mixed>\d+ \d+/\d+)|(?P<fraction>\d+/\d+)|(?P<number>\d[\d,]*(?:\.\d+)?)"
    r"|(?P<variable>[a-z])"
    r"|(?P<symbol>[-+*()\[\]\N{MINUS SIGN}\N{MULTIPLICATION SIGN}\N{DIVISION SIGN}]))"
)
_SIGNS = {
    "+": Operation.ADD,
    "-": Operation.SUBTRACT,
    MINUS: Operation.SUBTRACT,
    "*": Operation.MULTIPLY,
    "\N{MULTIPLICATION SIGN}": Operation.MULTIPLY,
    "\N{DIVISION SIGN}": Operation.DIVIDE,
}
_ADDING = (Operation.ADD, Operation.SUBTRACT)
_MULTIPLYING = (Operation.MULTIPLY, Operation.DIVIDE)
_GROUPS = {"(": (")", Grouping.PARENTHESES), "[": ("]", Grouping.BRACKETS)}

# A token ``parse`` reads: a number or variable, or a sign or grouping symbol as written
type _Token = Number | Variable | str


def value_pieces(value: NumberValue, money: bool = False) -> Pieces:
    """
    Return ``value`` as pieces, with commas between groups of three digits: a whole number as it
    is, 1,368; a decimal without trailing zeros, 2.7 and 100, or in ``money`` with two places,
    2.70 and 68.00; a fraction as a mixed number, 10 1/4, or a proper fraction, 1/4.

    Raises ``ValueError`` for money that isn't in whole cents, such as 3.625.
    """
    if not isinstance(value, Decimal):
        return number_pieces(value, NumberStyle.MIXED_NUMBER)
    sign = MINUS if value < 0 else ""
    size = abs(value)
    if not money:
        return (f"{sign}{size.normalize():,f}",)
    cents = size.quantize(_CENT)
    if cents != size:
        raise ValueError(f"{value} isn't in whole cents.")
    return (f"{sign}{cents:,f}",)


def expression_pieces(
    expression: Expression,
    money: bool = False,
    brackets: bool = True,
    sign_before_implied: bool = False,
) -> Pieces:
    """
    Return ``expression`` as pieces, its numbers written by ``value_pieces``, and its groups with
    their own symbols, or all in parentheses when ``brackets`` is off. ``sign_before_implied``
    lets a x or ÷ come just before a multiplication written without its sign: 60 ÷ 6[2 + 8].

    Raises ``ValueError`` if the text wouldn't read back as ``expression`` by the order of
    operations, if a sign is left out of anything but a multiplication beside a number, variable
    or group, if a x or ÷ comes just before one without ``sign_before_implied``, or if groups
    nest more than two deep, or ( ) around ( ) or [ ] inside a group when ``brackets`` is on.
    """
    pieces = merge_pieces(_pieces(expression, money, brackets, sign_before_implied))
    _check_nesting(pieces, brackets)
    return pieces


def expression_text(
    expression: Expression,
    money: bool = False,
    brackets: bool = True,
    sign_before_implied: bool = False,
) -> str:
    """Return ``expression`` written inline, as ``expression_pieces`` writes it."""
    return inline(expression_pieces(expression, money, brackets, sign_before_implied))


def parse(text: str) -> Expression:
    """
    Return the expression ``text`` writes, as ``expression_text`` would write it: signs, ( ) and
    [ ], a letter for the variable, a sign left out of a multiplication beside a group or letter,
    and numbers with commas, decimals, fractions such as 1/4 and mixed numbers such as 10 1/4.
    A hyphen is read as minus and * as times, and a multiplication without its sign is read
    before a x or ÷ beside it.

    Raises ``ValueError`` for text that isn't an expression.
    """
    tokens = _tokens(text)
    expression, position = _sum(tokens, 0, text)
    if position < len(tokens):
        raise ValueError(f"Unexpected {tokens[position]!r} in {text!r}.")
    return expression


def is_grouped(expression: Expression) -> TypeIs[Calculation]:
    """Return whether ``expression`` is a calculation with symbols around it."""
    return isinstance(expression, Calculation) and expression.grouping is not Grouping.NONE


def is_ungrouped(expression: Expression) -> TypeIs[Calculation]:
    """Return whether ``expression`` is a calculation without symbols around it."""
    return isinstance(expression, Calculation) and expression.grouping is Grouping.NONE


def _pieces(
    expression: Expression, money: bool, brackets: bool, sign_before_implied: bool
) -> list[Piece]:
    """Return ``expression``'s pieces, unmerged, checking that each calculation can be written."""
    match expression:
        case Number():
            return list(value_pieces(expression.value, money))
        case Variable():
            return [expression.name]
        case Calculation():
            if expression.implied:
                inside = _implied_pieces(expression, money, brackets, sign_before_implied)
            else:
                inside = _operation_pieces(expression, money, brackets, sign_before_implied)
            if expression.grouping is Grouping.NONE:
                return inside
            symbols = expression.grouping if brackets else Grouping.PARENTHESES
            return [_OPEN[symbols], *inside, _CLOSE[symbols]]
        case _:
            assert_never(expression)


def _operation_pieces(
    calculation: Calculation, money: bool, brackets: bool, sign_before_implied: bool
) -> list[Piece]:
    """Return ``calculation``'s pieces with its sign: an ungrouped side mustn't be read apart."""
    precedence = _precedence(calculation)
    left, right = calculation.left, calculation.right
    if (is_ungrouped(left) and _precedence(left) < precedence) or (
        is_ungrouped(right) and _precedence(right) <= precedence
    ):
        raise ValueError(
            "Without a group, part of this calculation would be read in another order."
        )
    # 60 ÷ 6[2 + 8] is 60 ÷ (6[2 + 8]), just as 60 over 6[2 + 8] is: the missing sign joins 6 to
    # the brackets. Read left to right, as (60 ÷ 6)[2 + 8], it's misread, and often enough that a
    # key built on the right reading gets marked wrong. So the form is written only on request,
    # for questions none of whose answers depend on it, as STAAR's one use (2025, the step where
    # an error first appears, inside the brackets) is.
    if (
        precedence == _PRECEDENCE[Operation.MULTIPLY]
        and is_ungrouped(right)
        and right.implied
        and not sign_before_implied
    ):
        raise ValueError(
            "A multiplication or division just before a multiplication without its sign is "
            "written only with sign_before_implied."
        )
    sign = f" {SYMBOLS[calculation.operation]} "
    return [
        *_pieces(left, money, brackets, sign_before_implied),
        sign,
        *_pieces(right, money, brackets, sign_before_implied),
    ]


def _implied_pieces(
    calculation: Calculation, money: bool, brackets: bool, sign_before_implied: bool
) -> list[Piece]:
    """
    Return the pieces of a multiplication written without its sign: each side a number, variable
    or group, or on the left another such multiplication, as in 3(4)(5). A number on the right
    is in parentheses, unless a group is on its left: 4(3), (31 + 41)8.
    """
    left, right = calculation.left, calculation.right
    if calculation.operation is not Operation.MULTIPLY:
        raise ValueError("Only a multiplication can leave out its sign.")
    if (is_ungrouped(left) and not left.implied) or is_ungrouped(right):
        raise ValueError(
            "A multiplication leaves out its sign only beside a number, variable or group."
        )
    right_pieces = _pieces(right, money, brackets, sign_before_implied)
    if isinstance(right, Number) and not is_grouped(left):
        right_pieces = ["(", *right_pieces, ")"]
    return [*_pieces(left, money, brackets, sign_before_implied), *right_pieces]


def _precedence(calculation: Calculation) -> int:
    """Return how early ``calculation`` is worked among those beside it: higher is earlier."""
    return _IMPLIED_PRECEDENCE if calculation.implied else _PRECEDENCE[calculation.operation]


def _check_nesting(pieces: Pieces, brackets: bool) -> None:
    """Raise ``ValueError`` if groups nest more than two deep, or as STAAR doesn't nest them."""
    open_symbols: list[str] = []
    for character in "".join(piece for piece in pieces if isinstance(piece, str)):
        if character in "([":
            if len(open_symbols) == 2:
                raise ValueError("Groups nest at most two deep.")
            if brackets and open_symbols and (character == "[" or open_symbols[-1] == "("):
                raise ValueError("Parentheses go inside brackets, and brackets inside nothing.")
            open_symbols.append(character)
        elif character in ")]":
            open_symbols.pop()


def _tokens(text: str) -> list[_Token]:
    """Return the numbers, letters and symbols ``text`` is made of."""
    tokens: list[_Token] = []
    position = 0
    while position < len(text.rstrip()):
        match = _TOKEN.match(text, position)
        if match is None:
            raise ValueError(f"Unexpected {text[position:].strip()!r} in {text!r}.")
        position = match.end()
        if match["mixed"]:
            whole, part = match["mixed"].split(" ")
            tokens.append(Number(int(whole) + Fraction(part)))
        elif match["fraction"]:
            tokens.append(Number(Fraction(match["fraction"])))
        elif match["number"]:
            digits = match["number"].replace(",", "")
            tokens.append(Number(Decimal(digits) if "." in digits else int(digits)))
        elif match["variable"]:
            tokens.append(Variable(match["variable"]))
        else:
            tokens.append(match["symbol"])
    return tokens


def _sum(tokens: list[_Token], position: int, text: str) -> tuple[Expression, int]:
    """Read terms joined by + and - from ``position``; return them and the position after."""
    expression, position = _product(tokens, position, text)
    while position < len(tokens):
        token = tokens[position]
        if not isinstance(token, str) or _SIGNS.get(token) not in _ADDING:
            break
        right, position = _product(tokens, position + 1, text)
        expression = Calculation(_SIGNS[token], expression, right)
    return expression, position


def _product(tokens: list[_Token], position: int, text: str) -> tuple[Expression, int]:
    """Read factors joined by x and ÷ from ``position``; return them and the position after."""
    expression, position = _side_by_side(tokens, position, text)
    while position < len(tokens):
        token = tokens[position]
        if not isinstance(token, str) or _SIGNS.get(token) not in _MULTIPLYING:
            break
        right, position = _side_by_side(tokens, position + 1, text)
        expression = Calculation(_SIGNS[token], expression, right)
    return expression, position


def _side_by_side(tokens: list[_Token], position: int, text: str) -> tuple[Expression, int]:
    """
    Read numbers, variables and groups side by side, multiplied without their signs, from
    ``position``; return them and the position after. A number is side by side only with a group
    before it: 4(3), (31 + 41)8, 3p.
    """
    expression, position, grouped = _factor(tokens, position, text)
    while position < len(tokens):
        token = tokens[position]
        if not (
            token in _GROUPS
            or isinstance(token, Variable)
            or (isinstance(token, Number) and grouped)
        ):
            break
        right, position, grouped = _factor(tokens, position, text)
        expression = Calculation(Operation.MULTIPLY, expression, right, implied=True)
    return expression, position


def _factor(tokens: list[_Token], position: int, text: str) -> tuple[Expression, int, bool]:
    """
    Read a number, variable or group from ``position``; return it, the position after, and
    whether it was a group. A group around a single number, as in 4(3), leaves just the number.
    """
    if position == len(tokens):
        raise ValueError(f"{text!r} ends too soon.")
    token = tokens[position]
    if isinstance(token, Number | Variable):
        return token, position + 1, False
    if token not in _GROUPS:
        raise ValueError(f"Unexpected {token!r} in {text!r}.")
    close, grouping = _GROUPS[token]
    inside, position = _sum(tokens, position + 1, text)
    if position == len(tokens) or tokens[position] != close:
        raise ValueError(f"{token!r} isn't closed by {close!r} in {text!r}.")
    if isinstance(inside, Calculation):
        inside = replace(inside, grouping=grouping)
    return inside, position + 1, True
