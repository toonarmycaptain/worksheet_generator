"""
The word-problem bank: the names, objects and templates that word a basic-operation question.

Every template takes the same slots, and may use any of them:
- ``{n1}`` and ``{n2}``: two different names;
- ``{a}`` and ``{b}``: the operands in presentation order;
- ``{obj}``: the object, plural, as in "How many {obj} are left?";
- ``{a_obj}`` and ``{b_obj}``: the object agreeing with ``{a}`` or ``{b}``, as in "{a} {a_obj}",
  which reads "1 sticker" or "5 stickers";
- ``{a:was|were}``, ``{b:page|pages}``: any other word that agrees with ``{a}`` or ``{b}``,
  singular first.

Addition and subtraction operands can be 1, so their templates use the agreeing slots wherever a
number meets a noun or a verb. Multiplication and division operands start at 2, so their
templates use ``{obj}``. A new template is one more string in its operation's tuple, and a new
operation is one more entry in ``TEMPLATES``.

Comparisons, which ask how many more one has than another, are kept apart in
``COMPARISON_TEMPLATES``: a part-part-whole picture, such as the strip diagram, can't show them.
"""

import random
from collections.abc import Sequence

from core.basic_operations.data import BasicOperationQuestionData, Operation

NAMES = (
    "Maria",
    "Jamal",
    "Priya",
    "Liam",
    "Sofia",
    "Chen",
    "Aisha",
    "Diego",
    "Emma",
    "Noah",
    "Zoe",
    "Omar",
    "Ava",
    "Kai",
    "Lucia",
    "Malik",
    "Hana",
    "Leo",
    "Nina",
    "Theo",
    "Rosa",
    "Sam",
    "Ivy",
    "Dev",
)
# Each object, singular and plural
OBJECTS = (
    ("sticker", "stickers"),
    ("marble", "marbles"),
    ("seashell", "seashells"),
    ("button", "buttons"),
    ("bead", "beads"),
    ("crayon", "crayons"),
    ("stamp", "stamps"),
    ("acorn", "acorns"),
    ("penny", "pennies"),
    ("book", "books"),
    ("apple", "apples"),
    ("pencil", "pencils"),
    ("bottle cap", "bottle caps"),
    ("leaf", "leaves"),
    ("coin", "coins"),
    ("block", "blocks"),
    ("card", "cards"),
)

TEMPLATES: dict[Operation, tuple[str, ...]] = {
    Operation.ADD: (
        "The library had {a} {a:book|books}. It received {b} more {b:book|books}. "
        "How many books does the library have now?",
        "A farm picked {a} {a:apple|apples} and then picked {b} more. "
        "How many apples were picked in all?",
        "{n1} collected {a} {a_obj}. {n2} collected {b} {b_obj}. "
        "How many {obj} did they collect altogether?",
        "There {a:was|were} {a} {a_obj} in the bin. {n1} put in {b} more. "
        "How many {obj} are in the bin now?",
        "{n1} had {a} {a_obj} and found {b} more. How many {obj} does {n1} have now?",
        "{n1} read {a} {a:page|pages} on Monday and {b} {b:page|pages} on Tuesday. "
        "How many pages in all?",
        "{n1} scored {a} {a:point|points}, then scored {b} more {b:point|points}. "
        "How many points in all?",
        "A basket held {a} {a_obj}. {n1} added {b} more. How many {obj} are in the basket now?",
    ),
    Operation.SUBTRACT: (
        "{n1} had {a} {a_obj}. {n1} gave away {b} of them. How many {obj} does {n1} have left?",
        "There {a:was|were} {a} {a_obj} on the shelf. {b} of them {b:was|were} sold. "
        "How many {obj} are left?",
        "{n1} had {a} {a_obj} and used {b}. How many {obj} are left?",
        "A book has {a} {a:page|pages}. {n1} has read {b} {b:page|pages}. "
        "How many pages are left to read?",
        "{n1} had {a} {a:point|points} and lost {b} {b:point|points}. "
        "How many points does {n1} have now?",
        "{n1} needs {a} {a_obj} in all and has {b} so far. How many more {obj} are needed?",
    ),
    # {a} groups of {b}: the whole is to find
    Operation.MULTIPLY: (
        "{n1} has {a} bags with {b} {obj} in each bag. How many {obj} are there in all?",
        "There are {a} boxes. Each box holds {b} {obj}. How many {obj} altogether?",
        "{n1} plants {a} rows with {b} flowers in each row. How many flowers did {n1} plant?",
        "Each basket has {b} {obj}. How many {obj} are in {a} baskets?",
        "{n1} buys {a} packs of {obj} with {b} in each pack. How many {obj} in all?",
        "{a} friends each have {b} {obj}. How many {obj} do they have together?",
    ),
    # {a} shared equally into {b} groups (partitive division): the size of each group is to find
    Operation.DIVIDE: (
        "{n1} shares {a} {obj} equally among {b} friends. How many {obj} does each friend get?",
        "{a} {obj} are put into {b} equal groups. How many {obj} are in each group?",
        "{n1} puts {a} {obj} into {b} baskets with the same number in each. "
        "How many {obj} per basket?",
        "{b} students share {a} {obj} equally. How many {obj} does each student get?",
        "{a} {obj} are placed in {b} equal rows. How many {obj} are in each row?",
        "{n1} divides {a} {obj} into {b} equal piles. How many {obj} are in each pile?",
    ),
}

# How many more {n1} has than {n2}: {a} is the larger amount
COMPARISON_TEMPLATES: dict[Operation, tuple[str, ...]] = {
    Operation.SUBTRACT: (
        "{n1} has {a} {a_obj} and {n2} has {b} {b_obj}. "
        "How many more {obj} does {n1} have than {n2}?",
    ),
}


class _Count(int):
    """
    A number in a template, which also gives the word that agrees with it: ``{a:was|were}`` is
    "was" when ``a`` is 1, and "were" otherwise. Any other format spec formats the number.
    """

    def __format__(self, spec: str) -> str:
        if "|" in spec:
            singular, plural = spec.split("|")
            return singular if self == 1 else plural
        return super().__format__(spec)


def word_problem_texts(
    questions: Sequence[BasicOperationQuestionData], *, comparisons: bool = False
) -> list[str]:
    """
    Word each question with a template for its operation, two different names and an object.

    With ``comparisons``, an operation's ``COMPARISON_TEMPLATES`` join its templates. No template
    is used twice for the same operation until all of that operation's templates have been used.
    """
    unused: dict[Operation, list[str]] = {}
    texts = []
    for data in questions:
        templates = unused.setdefault(data.operation, [])
        if not templates:
            pool = TEMPLATES[data.operation]
            if comparisons:
                pool += COMPARISON_TEMPLATES.get(data.operation, ())
            templates += random.sample(pool, len(pool))
        first_name, second_name = random.sample(NAMES, 2)
        singular, plural = random.choice(OBJECTS)
        first, second = data.operands
        text = templates.pop().format(
            n1=first_name,
            n2=second_name,
            obj=plural,
            a_obj=singular if first == 1 else plural,
            b_obj=singular if second == 1 else plural,
            a=_Count(first),
            b=_Count(second),
        )
        texts.append(text)
    return texts
