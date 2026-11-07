"""
The word-problem bank: the names, objects and templates that word a basic-operation question.

Every template takes the same slots: ``{n1}`` and ``{n2}``, two different names; ``{obj}``, a
plural object; and ``{a}`` and ``{b}``, the operands in presentation order. A template may use any
of them. A new template is one more string in its operation's tuple, and a new operation is one
more entry in ``TEMPLATES``.

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
OBJECTS = (
    "stickers",
    "marbles",
    "seashells",
    "buttons",
    "beads",
    "crayons",
    "stamps",
    "acorns",
    "pennies",
    "books",
    "apples",
    "pencils",
    "bottle caps",
    "leaves",
    "coins",
    "blocks",
    "cards",
)

TEMPLATES: dict[Operation, tuple[str, ...]] = {
    Operation.ADD: (
        "The library had {a} books. It received {b} more books. "
        "How many books does the library have now?",
        "A farm picked {a} apples and then picked {b} more. How many apples were picked in all?",
        "{n1} collected {a} {obj}. {n2} collected {b} {obj}. "
        "How many {obj} did they collect altogether?",
        "There were {a} {obj} in the bin. {n1} put in {b} more. How many {obj} are in the bin now?",
        "{n1} had {a} {obj} and found {b} more. How many {obj} does {n1} have now?",
        "{n1} read {a} pages on Monday and {b} pages on Tuesday. How many pages in all?",
        "{n1} scored {a} points, then scored {b} more points. How many points in all?",
        "A basket held {a} {obj}. {n1} added {b} more. How many {obj} are in the basket now?",
    ),
    Operation.SUBTRACT: (
        "{n1} had {a} {obj}. {n1} gave away {b} of them. How many {obj} does {n1} have left?",
        "There were {a} {obj} on the shelf. {b} of them were sold. How many {obj} are left?",
        "{n1} had {a} {obj} and used {b}. How many {obj} are left?",
        "A book has {a} pages. {n1} has read {b} pages. How many pages are left to read?",
        "{n1} had {a} points and lost {b} points. How many points does {n1} have now?",
        "{n1} needs {a} {obj} in all and has {b} so far. How many more {obj} are needed?",
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
        "{n1} has {a} {obj} and {n2} has {b} {obj}. How many more {obj} does {n1} have than {n2}?",
    ),
}


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
        first, second = data.operands
        text = templates.pop().format(
            n1=first_name, n2=second_name, obj=random.choice(OBJECTS), a=first, b=second
        )
        texts.append(text)
    return texts
