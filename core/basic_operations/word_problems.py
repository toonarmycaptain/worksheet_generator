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

New templates and objects go at the top of their tuples, and new names at the end. The tests
script ``random`` to take each tuple's templates from the end, the last object and the first two
names, so their wording stays the same. Comparisons are the exception: with comparisons on, the
tests take them first, so a new comparison changes the wording of any test with more problems of
its operation than there were comparisons.

Comparisons, which ask how many more one has than another, are kept apart in
``COMPARISON_TEMPLATES``: a part-part-whole representation, such as the strip diagram, can't show
them.

Two-step problems have their own templates, in ``TWO_STEP_TEMPLATES``, keyed by their shape. They
take the same slots, with ``{a}`` and ``{b}`` as the first step's operands, plus ``{c}``,
``{c_obj}`` and ``{c:...}`` for the second step's other operand. The first step's answer, which
the second step also uses, is never stated. The generator draws only the shapes that have an
entry, and each shape needs its strip diagram and wrong choices too, in
``core.basic_operations.representation``: so far, the five shapes that one bar can show.
"""

import random
from collections.abc import Sequence

from core.basic_operations.data import (
    BasicOperationQuestionData,
    Operation,
    TwoStepQuestionData,
    TwoStepShape,
    Unknown,
)

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
    "Mateo",
    "Grace",
    "Ravi",
    "Elena",
    "Jonah",
    "Mia",
    "Tariq",
    "Lily",
)
# Each object, singular and plural
OBJECTS = (
    ("eraser", "erasers"),
    ("toy car", "toy cars"),
    ("paper clip", "paper clips"),
    ("postcard", "postcards"),
    ("seed", "seeds"),
    ("magnet", "magnets"),
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
        "A school collected {a} {a:can|cans} of food on Monday and {b} {b:can|cans} on Tuesday. "
        "How many cans of food did the school collect in all?",
        "A parking lot had {a} {a:car|cars}. Then {b} more {b:car|cars} parked there. "
        "How many cars are in the parking lot now?",
        "A farm has {a} {a:cow|cows} and {b} {b:horse|horses}. How many animals are on the farm?",
        "The school play sold {a} {a:ticket|tickets} on Friday and {b} {b:ticket|tickets} on "
        "Saturday. How many tickets did the play sell in all?",
        "{n1} took {a} {a:step|steps} before lunch and {b} {b:step|steps} after lunch. "
        "How many steps did {n1} take in all?",
        "A museum had {a} {a:visitor|visitors} on Saturday and {b} {b:visitor|visitors} on "
        "Sunday. How many visitors did the museum have in all?",
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
        "The theater has {a} {a:seat|seats}. {b} of them {b:is|are} filled. "
        "How many seats are empty?",
        "A bus had {a} {a:passenger|passengers}. At the first stop, {b} {b:passenger|passengers} "
        "got off. How many passengers are on the bus now?",
        "{n1} had {a} {a_obj} and put {b} of them in a box. How many {obj} are not in the box?",
        "A store had {a} {a:bottle|bottles} of water and sold {b} of them. "
        "How many bottles of water does the store have left?",
        "A tree had {a} {a:leaf|leaves}. {b} {b:leaf|leaves} fell off. "
        "How many leaves are still on the tree?",
        "{n1} had {a} {a:dollar|dollars} and spent {b} {b:dollar|dollars}. "
        "How many dollars does {n1} have left?",
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
        "A classroom has {a} rows of desks with {b} desks in each row. "
        "How many desks are in the classroom?",
        "{n1} reads {b} pages each day for {a} days. How many pages does {n1} read in all?",
        "There are {a} teams with {b} players on each team. How many players are there in all?",
        "{n1} puts {b} {obj} in each of {a} jars. How many {obj} are in the jars?",
        "{n1} saves {b} dollars each week for {a} weeks. How many dollars does {n1} save in all?",
        "{a} tables each have {b} {obj} on them. How many {obj} are on the tables?",
        "{n1} has {a} bags with {b} {obj} in each bag. How many {obj} are there in all?",
        "There are {a} boxes. Each box holds {b} {obj}. How many {obj} altogether?",
        "{n1} plants {a} rows with {b} flowers in each row. How many flowers did {n1} plant?",
        "Each basket has {b} {obj}. How many {obj} are in {a} baskets?",
        "{n1} buys {a} packs of {obj} with {b} in each pack. How many {obj} in all?",
        "{a} friends each have {b} {obj}. How many {obj} do they have together?",
    ),
    # {a} shared equally into {b} groups (partitive division): the size of each group is to find
    Operation.DIVIDE: (
        "A coach puts {a} players into {b} teams with the same number on each team. "
        "How many players are on each team?",
        "{n1} reads {a} pages in {b} days, the same number each day. "
        "How many pages does {n1} read each day?",
        "{a} students sit at {b} tables, with the same number at each table. "
        "How many students sit at each table?",
        "{n1} packs {a} {obj} equally into {b} boxes. How many {obj} go in each box?",
        "{n1} saved {a} dollars in {b} weeks, the same amount each week. "
        "How many dollars did {n1} save each week?",
        "A baker puts {a} muffins on {b} trays with the same number on each tray. "
        "How many muffins are on each tray?",
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
        "{n1} scored {a} {a:point|points} and {n2} scored {b} {b:point|points}. "
        "How many more points did {n1} score than {n2}?",
        "{n1} has {a} {a_obj}. {n2} has {b} {b_obj}. "
        "How many fewer {obj} does {n2} have than {n1}?",
        "A school sold {a} {a:ticket|tickets} on Friday and {b} {b:ticket|tickets} on Saturday. "
        "How many more tickets were sold on Friday than on Saturday?",
        "{n1} has {a} {a_obj} and {n2} has {b} {b_obj}. "
        "How many more {obj} does {n1} have than {n2}?",
    ),
}

# {a} and {b} make the first step's answer, which the second step uses with {c}
TWO_STEP_TEMPLATES: dict[TwoStepShape, tuple[str, ...]] = {
    # ({a} + {b}) + {c}
    (Operation.ADD, Operation.ADD, Unknown.FIRST): (
        "A school sold {a} {a:ticket|tickets} on Friday, {b} on Saturday and {c} on Sunday. "
        "How many tickets did the school sell in all?",
        "{n1} had {a} {a_obj}. {n1} found {b} more on Monday and {c} more on Tuesday. "
        "How many {obj} does {n1} have now?",
        "A jar held {a} {a_obj}. {n1} added {b} more, and then {n2} added {c} more. "
        "How many {obj} are in the jar now?",
    ),
    # ({a} - {b}) - {c}
    (Operation.SUBTRACT, Operation.SUBTRACT, Unknown.FIRST): (
        "A bus had {a} {a:passenger|passengers}. {b} got off at the first stop, and {c} got off "
        "at the second stop. How many passengers are still on the bus?",
        "{n1} had {a} {a_obj}. {n1} gave {b} to {n2} and then lost {c}. "
        "How many {obj} does {n1} have left?",
        "A box held {a} {a_obj}. {n1} took out {b}, and then {n2} took out {c}. "
        "How many {obj} are left in the box?",
    ),
    # ({a} - {b}) shared equally into {c} groups
    (Operation.SUBTRACT, Operation.DIVIDE, Unknown.FIRST): (
        "A baker made {a} {a:muffin|muffins} and sold {b}. The baker put the rest on {c} trays "
        "with the same number on each tray. How many muffins are on each tray?",
        "{n1} has {a} {a_obj}. {n1} gives {b} to {n2} and then shares the rest equally among {c} "
        "friends. How many {obj} does each friend get?",
        "{n1} had {a} {a_obj} and used {b}. {n1} put the rest into {c} equal groups. "
        "How many {obj} are in each group?",
        "{n1} has {a} {a_obj}. {b} {b:is|are} in a box, and the rest are in {c} bags with the same "
        "number in each bag. How many {obj} are in each bag?",
    ),
    # ({a} groups of {b}) + {c}
    (Operation.MULTIPLY, Operation.ADD, Unknown.FIRST): (
        "{n1} bought {a} packs of {obj} with {b} in each pack. {n2} gave {n1} {c} more {c_obj}. "
        "How many {obj} does {n1} have now?",
        "{n1} has {a} bags with {b} {obj} in each bag, and {c} more {c_obj} on the table. "
        "How many {obj} does {n1} have in all?",
        "There are {a} boxes with {b} {obj} in each box. {n1} brings {c} more. "
        "How many {obj} are there now?",
    ),
    # {c} - ({a} groups of {b})
    (Operation.MULTIPLY, Operation.SUBTRACT, Unknown.SECOND): (
        "{n1} had {c} {c_obj} and put {b} in each of {a} boxes. How many {obj} are not in a box?",
        "{n1} had {c} {c_obj}. {n1} gave {a} friends {b} {obj} each. "
        "How many {obj} does {n1} have left?",
        "A store had {c} {c_obj}. It sold {a} packs with {b} {obj} in each pack. "
        "How many {obj} does the store have left?",
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
        pool = TEMPLATES[data.operation]
        if comparisons:
            pool += COMPARISON_TEMPLATES.get(data.operation, ())
        template = _next_template(unused.setdefault(data.operation, []), pool)
        texts.append(_fill(template, data.operands))
    return texts


def two_step_texts(questions: Sequence[TwoStepQuestionData]) -> list[str]:
    """
    Word each two-step question with a template for its shape, two different names and an
    object.

    No template is used twice for the same shape until all of that shape's templates have been
    used.
    """
    unused: dict[TwoStepShape, list[str]] = {}
    texts = []
    for data in questions:
        template = _next_template(unused.setdefault(data.shape, []), TWO_STEP_TEMPLATES[data.shape])
        texts.append(_fill(template, data.given_numbers))
    return texts


def _next_template(unused: list[str], pool: Sequence[str]) -> str:
    """Take a template from ``unused``, first refilling it with ``pool`` shuffled if it's empty."""
    if not unused:
        unused += random.sample(pool, len(pool))
    return unused.pop()


def _fill(template: str, numbers: Sequence[int]) -> str:
    """
    Fill ``template``'s slots with two different names, an object, and ``numbers`` in order as
    ``{a}``, ``{b}`` and ``{c}``, each with its agreeing object and words.
    """
    first_name, second_name = random.sample(NAMES, 2)
    singular, plural = random.choice(OBJECTS)
    slots: dict[str, object] = {}
    for slot, number in zip("abc", numbers, strict=False):
        slots[slot] = _Count(number)
        slots[f"{slot}_obj"] = singular if number == 1 else plural
    return template.format(n1=first_name, n2=second_name, obj=plural, **slots)
