"""
The topic bank for data sets: what a data set is about, and the words that describe it.

A categorical data set's topic is a survey, such as students' favorite fruit, or a friends topic,
such as the cans four friends collected. A numerical data set's topic is a list of numbers, such
as the number of students in each class. A new topic is one more entry in its tuple.

Number-list topics word their questions with two templates:
- ``intro``: ``{person}`` is the data set's ``person``, as in "{person}'s class measured…";
- ``phrase``: ``{amount}`` is one or more numbers with the topic's amount, as in "have 20
  students", "have 18 or 20 students" or "have 20 or more students".
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SurveyTopic:
    """
    A survey: students each choose one of ``categories``, and a category's count is the number of
    students who chose it.
    """

    title: str  # "Favorite Fruit", above each display
    category_header: str  # "Fruit", heading a table's categories
    favorite: str  # "fruit", as in "name their favorite fruit"
    categories: tuple[str, ...]  # plural and lower case: "How many students chose apples?"


@dataclass(frozen=True)
class FriendsTopic:
    """
    Four friends each count something, such as the cans each collected for a food drive. Each
    friend is a category, and their count is their number of ``unit``.

    A friends topic has no category header: its categories are always names.
    """

    title: str  # "Cans Collected", above each display
    unit: str  # "cans"
    unit_singular: str  # "can"
    verb: str  # "collect", as in "How many more cans did Maria collect than Leo?"
    verb_past: str  # "collected", as in "How many cans were collected in all?"
    intro: str  # "Four friends collected cans for a food drive."


@dataclass(frozen=True)
class NumberListTopic:
    """
    A list of numbers, one per data point, such as the number of students in each class, and the
    number line they're plotted on.

    ``ticks`` holds the numbers a number line can show for this topic, and a list's numbers come
    from a window of them. When ``possible_values`` is set, as for coins, the list holds only
    those numbers, and the number line shows every tick.
    """

    title: str  # "Students in Each Class", above each display
    axis_title: str  # "Number of Students", under the number line
    ticks: range
    unit: str  # "classes": what each number in the list stands for
    unit_singular: str  # "class"
    phrase: str  # "have {amount}", as in "How many classes have 20 students?"
    amount_singular: str  # "student"
    amount_plural: str  # "students"
    intro: str
    possible_values: tuple[int, ...] | None = None


CATEGORY_TOPICS: tuple[SurveyTopic | FriendsTopic, ...] = (
    SurveyTopic(
        title="Favorite Fruit",
        category_header="Fruit",
        favorite="fruit",
        categories=("apples", "bananas", "grapes", "oranges", "peaches", "strawberries"),
    ),
    SurveyTopic(
        title="Favorite Pet",
        category_header="Pet",
        favorite="pet",
        categories=("dogs", "cats", "fish", "birds", "hamsters", "rabbits"),
    ),
    SurveyTopic(
        title="Favorite Season",
        category_header="Season",
        favorite="season",
        categories=("spring", "summer", "fall", "winter"),
    ),
    SurveyTopic(
        title="Favorite Sport",
        category_header="Sport",
        favorite="sport",
        categories=("soccer", "basketball", "baseball", "swimming", "tennis", "football"),
    ),
    SurveyTopic(
        title="Favorite Color",
        category_header="Color",
        favorite="color",
        categories=("red", "blue", "green", "purple", "yellow", "orange"),
    ),
    SurveyTopic(
        title="Favorite Lunch",
        category_header="Lunch",
        favorite="lunch",
        categories=("pizza", "tacos", "pasta", "salad", "soup", "sandwiches"),
    ),
    FriendsTopic(
        title="Cans Collected",
        unit="cans",
        unit_singular="can",
        verb="collect",
        verb_past="collected",
        intro="Four friends collected cans for a food drive.",
    ),
    FriendsTopic(
        title="Books Read",
        unit="books",
        unit_singular="book",
        verb="read",
        verb_past="read",
        intro="Four friends kept track of how many books they read this year.",
    ),
    FriendsTopic(
        title="Points Scored",
        unit="points",
        unit_singular="point",
        verb="score",
        verb_past="scored",
        intro="Four friends played a game and kept track of their points.",
    ),
    FriendsTopic(
        title="Tickets Sold",
        unit="tickets",
        unit_singular="ticket",
        verb="sell",
        verb_past="sold",
        intro="Four friends sold tickets for the school play.",
    ),
)

NUMBER_LIST_TOPICS = (
    NumberListTopic(
        title="Students in Each Class",
        axis_title="Number of Students",
        ticks=range(15, 31),
        unit="classes",
        unit_singular="class",
        phrase="have {amount}",
        amount_singular="student",
        amount_plural="students",
        intro="The list shows how many students are in each class at {person}'s school.",
    ),
    NumberListTopic(
        title="Points per Game",
        axis_title="Number of Points",
        ticks=range(10, 41),
        unit="games",
        unit_singular="game",
        phrase="had {amount}",
        amount_singular="point",
        amount_plural="points",
        intro=(
            "The list shows how many points {person}'s basketball team scored in each game "
            "this season."
        ),
    ),
    NumberListTopic(
        title="Bean Plant Heights",
        axis_title="Height (inches)",
        ticks=range(5, 25),
        unit="plants",
        unit_singular="plant",
        phrase="are {amount} tall",
        amount_singular="inch",
        amount_plural="inches",
        intro=(
            "{person}'s class measured the height of each bean plant in inches. "
            "The list shows the results."
        ),
    ),
    NumberListTopic(
        title="Minutes to Get to School",
        axis_title="Number of Minutes",
        ticks=range(5, 61, 5),
        unit="students",
        unit_singular="student",
        phrase="take {amount} to get to school",
        amount_singular="minute",
        amount_plural="minutes",
        intro=(
            "{person} asked some students how many minutes it takes them to get to school. "
            "The list shows their answers."
        ),
    ),
    NumberListTopic(
        title="Coins in a Piggy Bank",
        axis_title="Value of Coin (cents)",
        ticks=range(0, 31, 5),
        unit="coins",
        unit_singular="coin",
        phrase="are worth {amount}",
        amount_singular="cent",
        amount_plural="cents",
        intro="{person} emptied a piggy bank. The list shows the value of each coin in cents.",
        possible_values=(5, 10, 25),
    ),
    NumberListTopic(
        title="Books Read This Year",
        axis_title="Number of Books",
        ticks=range(5, 31),
        unit="students",
        unit_singular="student",
        phrase="read {amount}",
        amount_singular="book",
        amount_plural="books",
        intro=(
            "{person} asked some students how many books they read this year. "
            "The list shows their answers."
        ),
    ),
)
