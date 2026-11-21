"""
What an order of operations question shows: its question, the expressions and steps under it,
the wording of its options, the answer key's entry, and on a self-check tiles sheet, the answer
as the bank shows it. Expressions are pieces, so a PDF can stack their fractions.
"""

from decimal import Decimal
from fractions import Fraction

from core.arithmetic_expressions.data import Calculation, Expression, Number, NumberValue, Variable
from core.arithmetic_expressions.evaluation import replaced, step, steps, value
from core.arithmetic_expressions.random_expressions import NumberKind
from core.arithmetic_expressions.representation import expression_pieces, value_pieces
from core.basic_operations.data import Operation
from core.basic_operations.representation import SYMBOLS
from core.order_of_operations.data import (
    ErrorChoice,
    FindErrorQuestionData,
    FirstChoice,
    FirstOperationQuestionData,
    FirstResultQuestionData,
    GroupSymbols,
    HasValueQuestionData,
    Improper,
    NextStepQuestionData,
    Order,
    Pair,
    ParenthesesQuestionData,
    QuestionType,
    Statement,
    StepBlankQuestionData,
    Then,
    Timing,
    ValueCountQuestionData,
    ValueOption,
    ValueQuestionData,
    Why,
)
from core.question import BLANK
from core.self_check_tiles import TileQuestion
from core.written_numbers import Pieces, inline, merge_pieces

ORDER_OF_OPERATIONS_NAME = "Order of Operations"
QUESTION_TYPE_NAMES = {
    QuestionType.VALUE: "Find the value",
    QuestionType.NEXT_STEP: "Choose the next step",
    QuestionType.HAS_VALUE: "Which has the value?",
    QuestionType.FIRST_OPERATION: "Which operation first?",
    QuestionType.PARENTHESES: "What the parentheses show",
    QuestionType.FIND_ERROR: "Find the error",
}
# How deeply groups nest, by level, with what it looks like
LEVEL_NAMES = {
    0: "No grouping: 20 \N{MINUS SIGN} 3 \N{MULTIPLICATION SIGN} 4 + 6",
    1: "One level: 8 \N{MULTIPLICATION SIGN} (3.8 + 13.2) \N{MINUS SIGN} 6",
    2: "Two levels: [45 \N{MINUS SIGN} (6 + 3)] \N{MULTIPLICATION SIGN} 27",
}
# How a group with a group inside it is written, with what it looks like
GROUP_SYMBOLS_NAMES = {
    GroupSymbols.BRACKETS: "Brackets: [(9 \N{MINUS SIGN} 5) \N{MULTIPLICATION SIGN} (3 + 7)]",
    GroupSymbols.PARENTHESES: "Parentheses: ((9 \N{MINUS SIGN} 5) \N{MULTIPLICATION SIGN} (3 + 7))",
    GroupSymbols.MIXED: "Mixed",
}
NUMBER_KIND_NAMES = {
    NumberKind.WHOLE: "Whole numbers",
    NumberKind.DECIMAL: "Decimals",
    NumberKind.FRACTION: "Fractions",
}
NOUNS = {
    Operation.ADD: "addition",
    Operation.SUBTRACT: "subtraction",
    Operation.MULTIPLY: "multiplication",
    Operation.DIVIDE: "division",
}
RESULTS = {
    Operation.ADD: "sum",
    Operation.SUBTRACT: "difference",
    Operation.MULTIPLY: "product",
    Operation.DIVIDE: "quotient",
}
REASONS = {
    Why.IN_PARENTHESES: "the operation in the parentheses should be performed first",
    Why.IN_BRACKETS: "the operation in the brackets should be performed first",
    Why.MULTIPLYING_FIRST: "multiplication and division should be performed before addition "
    "and subtraction",
    Why.LEFT_TO_RIGHT: "it is the first operation when reading left to right",
    Why.RIGHT_TO_LEFT: "it is the first operation when reading right to left",
}
EQUALS = " = "
# Written where a step's box goes, then swapped for it: no number on a sheet has five decimal
# places
_BOX_MARK = Decimal("0.00001")

# Any question's data
type OrderOfOperationsQuestionData = (
    ValueQuestionData
    | NextStepQuestionData
    | StepBlankQuestionData
    | HasValueQuestionData
    | ValueCountQuestionData
    | FirstOperationQuestionData
    | FirstResultQuestionData
    | ParenthesesQuestionData
    | FindErrorQuestionData
)
# The data of the forms a self-check tiles sheet asks
type TileQuestionData = (
    ValueQuestionData | StepBlankQuestionData | ValueCountQuestionData | FirstResultQuestionData
)
# An option of any question
type Option = ValueOption | Expression | FirstChoice | Statement | ErrorChoice


def question(data: OrderOfOperationsQuestionData, choices: bool) -> str:
    """
    Return the question, as STAAR words it where it asks it, worded for lettered choices with
    ``choices``, else for a written answer. The expression, steps or expressions to circle are
    drawn below it, not written in it.
    """
    match data:
        case ValueQuestionData():
            return "What is the value of this expression?"
        case NextStepQuestionData():
            if data.shown and choices:
                return (
                    "Which expressions are equivalent to the expression shown? Select TWO "
                    "correct answers."
                )
            if data.shown:
                return "Circle the two expressions that are equivalent to the expression shown."
            if choices:
                return "Which expression is equivalent to the expression shown?"
            return "Write the expression after the next step."
        case StepBlankQuestionData():
            return "What number goes in the box?"
        case HasValueQuestionData():
            has = "has" if data.has else "does NOT have"
            target = number_text(data.target)
            if choices:
                return f"Which expression {has} a value of {target}?"
            return f"Circle the expression that {has} a value of {target}."
        case ValueCountQuestionData():
            return f"How many of these expressions have a value of {number_text(data.target)}?"
        case FirstOperationQuestionData():
            asked = "Which operation should be performed first when simplifying this expression?"
            return asked if choices else f"{asked} Explain why."
        case FirstResultQuestionData():
            return "What number does the first operation give?"
        case ParenthesesQuestionData():
            if not choices:
                return "What do the parentheses tell you to do in this expression?"
            if isinstance(data.answer, Timing):
                return "Which statement is true about the parentheses in this expression?"
            return "What do these parentheses indicate in the expression?"
        case FindErrorQuestionData():
            asked = (
                "An expression is incorrectly simplified as shown. In which step does the error "
                "first appear?"
            )
            return asked if choices else f"{asked} Explain the error."


def shown_lines(data: OrderOfOperationsQuestionData) -> list[Pieces]:
    """
    Return the lines drawn under the question: the expression; for a step with a box, the
    expression equal to the step; for a worked simplification, the given expression and each
    step, labelled. None for questions whose expressions are the ones to choose from or circle.
    """
    match data:
        case HasValueQuestionData() | ValueCountQuestionData():
            return []
        case StepBlankQuestionData():
            return [
                merge_pieces([*_pieces(data.expression, data.brackets), EQUALS, *boxed_step(data)])
            ]
        case FindErrorQuestionData():
            lines = [merge_pieces(["Given: ", *_error_pieces(data, data.expression)])]
            for number, each in enumerate(data.steps, start=1):
                lines.append(merge_pieces([f"Step {number}: ", *_error_pieces(data, each)]))
            return lines
    return [_pieces(data.expression, data.brackets)]


def boxed_step(data: StepBlankQuestionData) -> Pieces:
    """Return the step with its left-out number written as a box, ``BLANK``, to write in."""
    pieces = _pieces(replaced(data.step, data.blank, Number(_BOX_MARK)), data.brackets)
    mark = number_text(_BOX_MARK)
    return tuple(
        piece.replace(mark, BLANK) if isinstance(piece, str) else piece for piece in pieces
    )


def circled(data: OrderOfOperationsQuestionData, choices: bool) -> list[Pieces]:
    """
    Return the expressions drawn without letters under a question, to circle or to count: the
    five to choose two from and the four to choose one from, when written, and the four to
    count. None otherwise.
    """
    match data:
        case NextStepQuestionData() if data.shown and not choices:
            return [_pieces(each, data.brackets) for each in data.shown]
        case HasValueQuestionData() if not choices:
            return [_pieces(each, data.brackets) for each in data.expressions]
        case ValueCountQuestionData():
            return [_pieces(each, data.brackets) for each in data.expressions]
    return []


def option_pieces(data: OrderOfOperationsQuestionData, option: Option) -> Pieces:
    """
    Return a lettered choice as written: a value, an improper fraction as STAAR writes the wrong
    one it comes from, an expression in the question's symbols, or a sentence.
    """
    match option:
        case Improper():
            return (option.value,)
        case int() | Decimal() | Fraction():
            return value_pieces(option)
        case Number() | Variable() | Calculation():
            return _pieces(option, data.brackets)
        case FirstChoice():
            return (first_choice_text(option),)
        case Order() | Timing():
            return (statement_text(option),)
        case ErrorChoice():
            return (error_choice_text(option),)


def number_text(number: NumberValue) -> str:
    """Return a number written inline: 1,368, 2.7, 10 1/4."""
    return inline(value_pieces(number))


def pair_text(pair: Pair) -> str:
    """Return a pair as written: "72 - 6", with the minus sign."""
    return f"{number_text(pair.left)} {SYMBOLS[pair.operation]} {number_text(pair.right)}"


def first_choice_text(choice: FirstChoice) -> str:
    """Return a first operation with its reason, as STAAR words it: "5 + 3, because ..."."""
    if choice.why is Why.BEFORE:
        assert choice.over is not None
        reason = f"{NOUNS[choice.pair.operation]} should be performed before {NOUNS[choice.over]}"
    else:
        reason = REASONS[choice.why]
    return f"{pair_text(choice.pair)}, because {reason}"


def statement_text(statement: Statement) -> str:
    """
    Return a statement about the parentheses, as STAAR words them: "Subtract 6 from 72 before
    multiplying by 4", or "The parentheses indicate that 8 + 2 should be solved first."
    """
    if isinstance(statement, Timing):
        when = "first" if statement.first else "last"
        return f"The parentheses indicate that {pair_text(statement.pair)} should be solved {when}."
    first = statement.first
    if isinstance(statement.then, Pair):
        after = _doing(statement.then)
    else:
        after = _doing_with_result(statement.then, first.operation)
    return f"{_do(first)} before {after}"


def error_choice_text(choice: ErrorChoice) -> str:
    """
    Return a step said to hold the error, with its reason: "Step 2, because 2 + 8 should be
    simplified first", or "Step 3, because 5 + 1.2 = 6.2".
    """
    if choice.equals is not None:
        (pair,) = choice.pairs
        return f"Step {choice.step}, because {pair_text(pair)} = {number_text(choice.equals)}"
    pairs = " and ".join(pair_text(pair) for pair in choice.pairs)
    return f"Step {choice.step}, because {pairs} should be simplified first"


def solution(data: OrderOfOperationsQuestionData) -> str:
    """
    Return the answer key's entry, after the correct letters for lettered choices: the answer,
    with the working that shows it where it helps.
    """
    match data:
        case ValueQuestionData():
            return f"{number_text(data.answer)}: {_working(data.expression, data.brackets)}"
        case NextStepQuestionData():
            joined = " and " if data.shown else ", or "
            return joined.join(_text(each, data.brackets) for each in data.answer)
        case StepBlankQuestionData():
            filled = _text(data.step, data.brackets)
            return f"{number_text(data.answer)}: {_text(data.expression, data.brackets)} = {filled}"
        case HasValueQuestionData():
            values = "; ".join(_valued(each, data.brackets) for each in data.expressions)
            return f"{_text(data.answer, data.brackets)}. {values}"
        case ValueCountQuestionData():
            values = "; ".join(_valued(each, data.brackets) for each in data.expressions)
            return f"{data.answer}: {values}"
        case FirstOperationQuestionData():
            return first_choice_text(data.answer)
        case FirstResultQuestionData():
            return (
                f"{number_text(data.answer)}: {pair_text(data.pair)} = {number_text(data.answer)}"
            )
        case ParenthesesQuestionData():
            return statement_text(data.answer)
        case FindErrorQuestionData():
            index = data.answer.step - 1
            before = data.steps[index - 1] if index else data.expression
            right = (
                step(before)
                if isinstance(data.steps[index], Calculation)
                else Number(value(before))
            )
            should = _error_text(data, right)
            return f"{error_choice_text(data.answer)}. Step {data.answer.step} should be {should}."


def tile_answer(data: OrderOfOperationsQuestionData) -> str:
    """Return the answer as the self-check tiles bank shows it, inline: "972", "10 1/4"."""
    return inline(tile_answer_pieces(data))


def tile_answer_pieces(data: OrderOfOperationsQuestionData) -> Pieces:
    """Return the answer as the self-check tiles bank draws it, its fractions stacked."""
    match data:
        case ValueCountQuestionData():
            return (str(data.answer),)
        case ValueQuestionData() | StepBlankQuestionData() | FirstResultQuestionData():
            return value_pieces(data.answer)
    raise ValueError("Only a tiles form's answer is in the bank.")


def order_of_operations_tile_question(data: TileQuestionData) -> TileQuestion:
    """
    Convert a tiles form's data to a ``TileQuestion``: the prompt is the question, the answer as
    the bank shows it, and the solution the answer key's entry.
    """
    return TileQuestion(
        prompt=question(data, choices=False), answer=tile_answer(data), solution=solution(data)
    )


def _do(pair: Pair) -> str:
    """Return an instruction to work ``pair``: "Subtract 6 from 72", "Multiply 4 by 72"."""
    left, right = number_text(pair.left), number_text(pair.right)
    match pair.operation:
        case Operation.ADD:
            return f"Add {left} and {right}"
        case Operation.SUBTRACT:
            return f"Subtract {right} from {left}"
        case Operation.MULTIPLY:
            return f"Multiply {left} by {right}"
        case Operation.DIVIDE:
            return f"Divide {left} by {right}"


def _doing(pair: Pair) -> str:
    """Return working ``pair`` as done after something: "subtracting 6 from 72"."""
    left, right = number_text(pair.left), number_text(pair.right)
    match pair.operation:
        case Operation.ADD:
            return f"adding {left} and {right}"
        case Operation.SUBTRACT:
            return f"subtracting {right} from {left}"
        case Operation.MULTIPLY:
            return f"multiplying {left} by {right}"
        case Operation.DIVIDE:
            return f"dividing {left} by {right}"


def _doing_with_result(then: Then, first: Operation) -> str:
    """
    Return what's done with the first result: "multiplying by 4", "adding 4", "subtracting 6",
    or with the result on the right, "subtracting the sum from 72", "dividing 40 by the sum".
    """
    number = number_text(then.number)
    result = RESULTS[first]
    match then.operation:
        case Operation.ADD:
            return f"adding {number}"
        case Operation.SUBTRACT:
            return (
                f"subtracting {number}"
                if then.result_left
                else (f"subtracting the {result} from {number}")
            )
        case Operation.MULTIPLY:
            return f"multiplying by {number}"
        case Operation.DIVIDE:
            return (
                f"dividing by {number}"
                if then.result_left
                else (f"dividing {number} by the {result}")
            )


def _pieces(expression: Expression, brackets: bool) -> Pieces:
    """Return ``expression`` as pieces, a group with a group inside in brackets if ``brackets``."""
    return expression_pieces(expression, brackets=brackets)


def _text(expression: Expression, brackets: bool) -> str:
    """Return ``expression`` written inline, as ``_pieces`` writes it."""
    return inline(_pieces(expression, brackets))


def _valued(expression: Expression, brackets: bool) -> str:
    """Return ``expression`` and its value: "(36 - 3) x 4 = 132"."""
    return f"{_text(expression, brackets)} = {number_text(value(expression))}"


def _working(expression: Expression, brackets: bool) -> str:
    """Return ``expression``'s working, one operation at a time: "28 + 7 x (12 - 4) = ..."."""
    return " = ".join(_text(each, brackets) for each in (expression, *steps(expression)))


def _error_pieces(data: FindErrorQuestionData, expression: Expression) -> Pieces:
    """Return a line of a worked simplification as pieces, as the question writes its lines."""
    return expression_pieces(
        expression, brackets=data.brackets, sign_before_implied=data.sign_before_implied
    )


def _error_text(data: FindErrorQuestionData, expression: Expression) -> str:
    """Return a line of a worked simplification written inline."""
    return inline(_error_pieces(data, expression))
