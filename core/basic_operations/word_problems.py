"""
The word-problem bank: the names, objects and templates that word a basic-operation question.

Every template takes the same slots: ``{n1}`` and ``{n2}``, two different names; ``{obj}``, a
plural object; and ``{a}`` and ``{b}``, the operands in presentation order. A template may use any
of them. A new template is one more string in its operation's tuple, and a new operation is one
more entry in ``TEMPLATES``.
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
}


def word_problem_texts(questions: Sequence[BasicOperationQuestionData]) -> list[str]:
    """
    Word each question with a template for its operation, two different names and an object.

    No template is used twice for the same operation until all of that operation's templates
    have been used.
    """
    unused: dict[Operation, list[str]] = {}
    texts = []
    for data in questions:
        templates = unused.setdefault(data.operation, [])
        if not templates:
            templates += random.sample(TEMPLATES[data.operation], len(TEMPLATES[data.operation]))
        first_name, second_name = random.sample(NAMES, 2)
        first, second = data.operands
        text = templates.pop().format(
            n1=first_name, n2=second_name, obj=random.choice(OBJECTS), a=first, b=second
        )
        texts.append(text)
    return texts
