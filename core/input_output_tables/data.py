"""
Data for input-output tables: number pairs that follow a rule about a real situation, and
questions that ask for the table or for its rule.
"""

from dataclasses import dataclass
from enum import StrEnum

from core.basic_operations.data import Operation
from core.input_output_tables.contexts import TableContext
from core.question import FreeResponse, MultipleChoice, Question, QuestionData

# A table's number pairs, in order, each as (input, output)
type NumberPairs = tuple[tuple[int, int], ...]
# A rule, as (operation, number): each output is its input operation number
type Rule = tuple[Operation, int]


class Blanks(StrEnum):
    """
    The cells a table to complete leaves out. Values are stable identifiers for the API and
    storage.
    """

    INPUTS = "inputs"  # inputs only
    OUTPUTS = "outputs"  # outputs only
    INPUTS_AND_OUTPUTS = "inputs_and_outputs"  # some of each


class ChoiceType(StrEnum):
    """
    A kind of question asked on a multiple-choice sheet, as STAAR asks them. Values are stable
    identifiers for the API and storage.
    """

    TABLE = "table"  # the rule given: choose the table that follows it
    SENTENCE = "sentence"  # the table given: complete a sentence by circling its rule's parts
    STATEMENT = "statement"  # the table given: choose the true statement of its rule


class RuleForm(StrEnum):
    """
    How a question asking for a table's rule shows the rules to choose from. Values are stable
    identifiers for the API and storage.
    """

    SENTENCE = "sentence"  # one sentence, its operations and numbers stacked to circle
    STATEMENT = "statement"  # lettered statements of the rules
    EXPLAINED = "explained"  # lettered facts, each with its rule as the reason: "..., because ..."


@dataclass(frozen=True)
class InputOutputTableQuestionData(QuestionData[NumberPairs]):
    """
    A table of number pairs that follow a rule about a real situation, ``context``: each output
    is its input ``operation`` ``number``. The rule is given, and ``answer`` holds the complete
    table's pairs.

    Addition and multiplication take the context's smaller quantity to its larger, so the smaller
    quantity is the input; subtraction and division take the larger to the smaller. ``name``
    fills the context's ``{name}`` slot, and is ``None`` when the context has none.

    ``blank_inputs`` and ``blank_outputs`` hold the indexes, in ascending order, of the pairs
    whose input or output is left out for the student to fill in. No pair has both left out. A
    multiple-choice question shows complete tables, so it leaves out none.
    """

    context: TableContext
    name: str | None
    operation: Operation
    number: int
    answer: NumberPairs
    blank_inputs: tuple[int, ...] = ()
    blank_outputs: tuple[int, ...] = ()


@dataclass(frozen=True)
class InputOutputRuleQuestionData(QuestionData[Rule]):
    """
    A complete table of number pairs, ``pairs``, about a real situation, ``context``, that asks
    for the rule they follow: ``answer``, each output being its input ``operation`` ``number``.
    ``form`` is how the rules to choose from are shown. ``name`` is as for
    ``InputOutputTableQuestionData``.
    """

    context: TableContext
    name: str | None
    pairs: NumberPairs
    answer: Rule
    form: RuleForm

    @property
    def operation(self) -> Operation:
        """The rule's operation, as ``InputOutputTableQuestionData`` has it."""
        return self.answer[0]

    @property
    def number(self) -> int:
        """The rule's number, as ``InputOutputTableQuestionData`` has it."""
        return self.answer[1]


# Either kind of question's data, for what both show: the rule's wording, the title, the headings
type InputOutputQuestionData = InputOutputTableQuestionData | InputOutputRuleQuestionData

# A table as presented: completed in writing, or chosen from lettered tables
type InputOutputTableQuestion = Question[
    InputOutputTableQuestionData, FreeResponse | MultipleChoice[NumberPairs]
]
# A table's rule as presented: chosen from rules, shown as a sentence to circle or as statements
type InputOutputRuleQuestion = Question[InputOutputRuleQuestionData, MultipleChoice[Rule]]
# Any question on an input-output tables sheet
type InputOutputQuestion = InputOutputTableQuestion | InputOutputRuleQuestion
