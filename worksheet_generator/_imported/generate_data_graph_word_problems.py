#!/usr/bin/env python3
"""Data and graphs worksheets: read a graph, complete another, solve (Grade 3).

Each problem is one data set with 4 categories (a survey or a "four friends"
tally), shown in one of four ways:
  * frequency table
  * pictograph   (key: each star = 2, 5 or 10; a half star is half of that)
  * bar graph    (scaled intervals of 2, 5 or 10; bars may end between lines)
  * dot plot     (each X = 1)
or, once per 4 problems, numerical data: a scrambled list of numbers (class
sizes, coin values in cents, ...) to show on a number-line dot plot.

The student then:
  a. uses the given model to complete a DIFFERENT model of the same data
     (2 of the 4 categories are left blank to fill in; from a list, the
     whole dot plot)                                         -- TEKS 3.8(A)
  b. solves a one-step problem (how many more / fewer / in all) -- TEKS 3.8(B)
  c. solves a two-step problem (e.g. two categories combined vs a third,
     or "how many have 20 or more")

On a 4-problem sheet each model is the one to complete once, and a model is
never paired with itself. Category counts are distinct (no ties) and always
fit the scale: multiples of the scale or a half step.

Texas TEKS 3.8(A): summarize a data set with multiple categories using a
frequency table, dot plot, pictograph, or bar graph with scaled intervals.
Texas TEKS 3.8(B): solve one- and two-step problems using categorical data
represented with a frequency table, dot plot, pictograph, or bar graph with
scaled intervals.

Usage (no install needed, via uv):
    uv run --with reportlab generate_data_graph_word_problems.py --seed 1 --label "Sheet A" --out A.pdf
"""

from __future__ import annotations

import argparse
import math
import os
import random

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from . import wp_common as wp

LINE = HexColor("#2d3748")
STAR = HexColor("#2b6cb0")
BAR_FILL = HexColor("#cfe3f7")
HEAD_FILL = HexColor("#edf2f7")
GRID = HexColor("#cbd5e0")
GRAY = HexColor("#718096")
PANEL_H = 150
MODELS = ["table", "pictograph", "bar_graph", "dot_plot"]
MODEL_NAME = {
    "table": "frequency table",
    "pictograph": "pictograph",
    "bar_graph": "bar graph",
    "dot_plot": "dot plot",
    "list": "list",
    "number_line": "dot plot",
}

# ---------------------------------------------------------------- problem bank
# "survey": students each choose a category; "tally": four friends each count something.
TOPICS = [
    {
        "kind": "survey",
        "title": "Favorite Fruit",
        "category_header": "Fruit",
        "favorite": "fruit",
        "categories": ["apples", "bananas", "grapes", "oranges", "peaches", "strawberries"],
    },
    {
        "kind": "survey",
        "title": "Favorite Pet",
        "category_header": "Pet",
        "favorite": "pet",
        "categories": ["dogs", "cats", "fish", "birds", "hamsters", "rabbits"],
    },
    {
        "kind": "survey",
        "title": "Favorite Season",
        "category_header": "Season",
        "favorite": "season",
        "categories": ["spring", "summer", "fall", "winter"],
    },
    {
        "kind": "survey",
        "title": "Favorite Sport",
        "category_header": "Sport",
        "favorite": "sport",
        "categories": ["soccer", "basketball", "baseball", "swimming", "tennis", "football"],
    },
    {
        "kind": "survey",
        "title": "Favorite Color",
        "category_header": "Color",
        "favorite": "color",
        "categories": ["red", "blue", "green", "purple", "yellow", "orange"],
    },
    {
        "kind": "survey",
        "title": "Favorite Lunch",
        "category_header": "Lunch",
        "favorite": "lunch",
        "categories": ["pizza", "tacos", "pasta", "salad", "soup", "sandwiches"],
    },
    {
        "kind": "tally",
        "title": "Cans Collected",
        "category_header": "Name",
        "unit": "cans",
        "unit_singular": "can",
        "verb": "collect",
        "verb_past": "collected",
        "intro": "Four friends collected cans for a food drive.",
    },
    {
        "kind": "tally",
        "title": "Books Read",
        "category_header": "Name",
        "unit": "books",
        "unit_singular": "book",
        "verb": "read",
        "verb_past": "read",
        "intro": "Four friends kept track of how many books they read this year.",
    },
    {
        "kind": "tally",
        "title": "Points Scored",
        "category_header": "Name",
        "unit": "points",
        "unit_singular": "point",
        "verb": "score",
        "verb_past": "scored",
        "intro": "Four friends played a game and kept track of their points.",
    },
    {
        "kind": "tally",
        "title": "Tickets Sold",
        "category_header": "Name",
        "unit": "tickets",
        "unit_singular": "ticket",
        "verb": "sell",
        "verb_past": "sold",
        "intro": "Four friends sold tickets for the school play.",
    },
]

# Numerical data: a scrambled list of numbers -> dot plot on a number line.
# Most topics give a realistic range (low..high by step); each problem uses a
# window of 6-18 numbers from it as the number line. Coins are fixed: the list
# only has 5, 10 and 25 ("possible_values"), but the number line ("ticks") also
# shows 0, 15, 20 and 30. Values are mostly 2-digit.
#   unit:   what each X stands for ("classes")
#   amount: what the number counts ("students"), used in phrases like "have 20 students"
MIN_TICKS, MAX_TICKS = 6, 18
LIST_STYLES = ["grid", "commas"]
NUMBER_TOPICS = [
    {
        "title": "Students in Each Class",
        "axis_title": "Number of Students",
        "low": 15,
        "high": 30,
        "step": 1,
        "unit": "classes",
        "unit_singular": "class",
        "phrase": "have {amount}",
        "amount_singular": "student",
        "amount_plural": "students",
        "intro": "The list shows how many students are in each class at {name}'s school.",
    },
    {
        "title": "Points per Game",
        "axis_title": "Number of Points",
        "low": 10,
        "high": 40,
        "step": 1,
        "unit": "games",
        "unit_singular": "game",
        "phrase": "had {amount}",
        "amount_singular": "point",
        "amount_plural": "points",
        "intro": "The list shows how many points {name}'s basketball team scored in each game this season.",
    },
    {
        "title": "Bean Plant Heights",
        "axis_title": "Height (inches)",
        "low": 5,
        "high": 24,
        "step": 1,
        "unit": "plants",
        "unit_singular": "plant",
        "phrase": "are {amount} tall",
        "amount_singular": "inch",
        "amount_plural": "inches",
        "intro": "{name}'s class measured the height of each bean plant in inches. The list shows the results.",
    },
    {
        "title": "Minutes to Get to School",
        "axis_title": "Number of Minutes",
        "low": 5,
        "high": 60,
        "step": 5,
        "unit": "students",
        "unit_singular": "student",
        "phrase": "take {amount} to get to school",
        "amount_singular": "minute",
        "amount_plural": "minutes",
        "intro": "{name} asked some students how many minutes it takes them to get to school. "
        "The list shows their answers.",
    },
    {
        "title": "Coins in a Piggy Bank",
        "axis_title": "Value of Coin (cents)",
        "ticks": range(0, 31, 5),
        "possible_values": [5, 10, 25],
        "unit": "coins",
        "unit_singular": "coin",
        "phrase": "are worth {amount}",
        "amount_singular": "cent",
        "amount_plural": "cents",
        "intro": "{name} emptied a piggy bank. The list shows the value of each coin in cents.",
    },
    {
        "title": "Books Read This Year",
        "axis_title": "Number of Books",
        "low": 5,
        "high": 30,
        "step": 1,
        "unit": "students",
        "unit_singular": "student",
        "phrase": "read {amount}",
        "amount_singular": "book",
        "amount_plural": "books",
        "intro": "{name} asked some students how many books they read this year. The list shows their answers.",
    },
]

# Question templates for category data; {first}/{second}/{third} are category names.
ONE_STEP = {
    "survey": {
        "more": "How many more students chose {first} than chose {second}?",
        "fewer": "How many fewer students chose {second} than chose {first}?",
        "or": "How many students chose {first} or {second}?",
    },
    "tally": {
        "more": "How many more {unit} did {first} {verb} than {second}?",
        "fewer": "How many fewer {unit} did {second} {verb} than {first}?",
        "or": "How many {unit} did {first} and {second} {verb} in all?",
    },
}
TWO_STEP = {
    "survey": {
        "combo_more": "How many more students chose {first} or {second} than chose {third}?",
        "more_combo": "How many more students chose {first} than chose {second} or {third}?",
        "not": "How many students did NOT choose {first}?",
        "all": "How many students answered the question in all?",
    },
    "tally": {
        "combo_more": "How many more {unit} did {first} and {second} {verb} together than {third}?",
        "more_combo": "How many more {unit} did {first} {verb} than {second} and {third} together?",
        "not": "How many {unit} did everyone except {first} {verb} in all?",
        "all": "How many {unit} were {verb_past} in all?",
    },
}


def model_pairs(rng, n):
    """(given model, target model) pairs, never a model paired with itself. The target
    is the model to complete (or, in the MC version, to pick). Targets are a rotation
    of the given models, so each model is the target once per 4. The pair that would
    end in a dot plot becomes list -> number-line dot plot (numerical data)."""
    given_order = rng.sample(MODELS, len(MODELS))
    shift = rng.randint(1, len(MODELS) - 1)
    pairs = []
    for i in range(n):
        position = i % len(MODELS)
        given_model = given_order[position]
        target_model = given_order[(position + shift) % len(MODELS)]
        pairs.append(
            ("list", "number_line") if target_model == "dot_plot" else (given_model, target_model)
        )
    return pairs


def _category_counts(rng, given_model, target_model, scale):
    """4 distinct counts that fit both models: dot plots stay within 10 Xs,
    pictographs within 8 stars; a half step is allowed when the scale is even."""
    if "dot_plot" in (given_model, target_model):
        allowed = list(range(1, 11))
    else:
        smallest_step = scale // 2 if scale % 2 == 0 else scale
        allowed = list(range(smallest_step, 8 * scale + 1, smallest_step))
    return rng.sample(allowed, 4)


# ------------------------------------------------------------------ questions
def _amount(topic, number):
    """'20 students', '1 cent'."""
    return f"{number} {topic['amount_singular'] if number == 1 else topic['amount_plural']}"


def _number_one_step(rng, dataset):
    topic, counts, ticks = dataset["topic"], dataset["counts"], dataset["ticks"]
    used = [i for i, count in enumerate(counts) if count]  # numbers that are in the list
    bigger, smaller = rng.sample(used, 2)
    if counts[bigger] < counts[smaller]:
        bigger, smaller = smaller, bigger
    if counts[bigger] != counts[smaller] and rng.random() < 0.6:
        bigger_phrase = topic["phrase"].format(amount=_amount(topic, ticks[bigger]))
        smaller_phrase = topic["phrase"].format(amount=_amount(topic, ticks[smaller]))
        answer = counts[bigger] - counts[smaller]
        return {
            "text": f"How many more {topic['unit']} {bigger_phrase} than {smaller_phrase}?",
            "answer": answer,
            "work": f"{counts[bigger]} − {counts[smaller]} = {answer}",
        }
    first, second = sorted((bigger, smaller))
    phrase = topic["phrase"].format(
        amount=f"{ticks[first]} or {ticks[second]} {topic['amount_plural']}"
    )
    answer = counts[first] + counts[second]
    return {
        "text": f"How many {topic['unit']} {phrase}?",
        "answer": answer,
        "work": f"{counts[first]} + {counts[second]} = {answer}",
    }


def _number_two_step(rng, dataset):
    topic, counts, ticks = dataset["topic"], dataset["counts"], dataset["ticks"]
    used = [i for i, count in enumerate(counts) if count]
    candidates = []  # (kind, text, answer, work)
    for threshold in used[1:-1]:  # thresholds that split the data
        for word, included in (
            ("more", [i for i in used if i >= threshold]),
            ("fewer", [i for i in used if i <= threshold]),
        ):
            phrase = topic["phrase"].format(
                amount=f"{ticks[threshold]} or {word} {topic['amount_plural']}"
            )
            answer = sum(counts[i] for i in included)
            candidates.append(
                (
                    f"or_{word}",
                    f"How many {topic['unit']} {phrase}?",
                    answer,
                    " + ".join(str(counts[i]) for i in included) + f" = {answer}",
                )
            )
    for third in used:
        rest = [i for i in used if i != third]
        for x in range(len(rest)):
            for y in range(x + 1, len(rest)):
                first, second = rest[x], rest[y]
                combined = counts[first] + counts[second]
                if combined > counts[third]:
                    pair_phrase = topic["phrase"].format(
                        amount=f"{ticks[first]} or {ticks[second]} {topic['amount_plural']}"
                    )
                    third_phrase = topic["phrase"].format(amount=_amount(topic, ticks[third]))
                    candidates.append(
                        (
                            "combo_more",
                            f"How many more {topic['unit']} {pair_phrase} than {third_phrase}?",
                            combined - counts[third],
                            f"{counts[first]} + {counts[second]} = {combined},  "
                            f"{combined} − {counts[third]} = {combined - counts[third]}",
                        )
                    )
    kind = rng.choice(sorted({candidate[0] for candidate in candidates}))
    _, text, answer, work = rng.choice(
        [candidate for candidate in candidates if candidate[0] == kind]
    )
    return {"text": text, "answer": answer, "work": work}


def _one_step_question(rng, dataset):
    if dataset["kind"] == "numbers":
        return _number_one_step(rng, dataset)
    topic, names, counts = dataset["topic"], dataset["question_names"], dataset["counts"]
    kind = rng.choice(list(ONE_STEP[topic["kind"]]))
    bigger, smaller = rng.sample(range(4), 2)
    if counts[bigger] < counts[smaller]:
        bigger, smaller = smaller, bigger
    if kind == "or":
        answer = counts[bigger] + counts[smaller]
        work = f"{counts[bigger]} + {counts[smaller]} = {answer}"
    else:
        answer = counts[bigger] - counts[smaller]
        work = f"{counts[bigger]} − {counts[smaller]} = {answer}"
    text = ONE_STEP[topic["kind"]][kind].format(first=names[bigger], second=names[smaller], **topic)
    return {"text": text, "answer": answer, "work": work}


def _two_step_question(rng, dataset):
    if dataset["kind"] == "numbers":
        return _number_two_step(rng, dataset)
    topic, names, counts = dataset["topic"], dataset["question_names"], dataset["counts"]
    candidates = []  # (kind, (first, second, third), answer, work)
    for third in range(4):
        rest = [i for i in range(4) if i != third]
        for first, second in [(rest[0], rest[1]), (rest[0], rest[2]), (rest[1], rest[2])]:
            combined = counts[first] + counts[second]
            if combined > counts[third]:
                candidates.append(
                    (
                        "combo_more",
                        (first, second, third),
                        combined - counts[third],
                        f"{counts[first]} + {counts[second]} = {combined},  "
                        f"{combined} − {counts[third]} = {combined - counts[third]}",
                    )
                )
            if counts[third] > combined:
                candidates.append(
                    (
                        "more_combo",
                        (third, first, second),
                        counts[third] - combined,
                        f"{counts[first]} + {counts[second]} = {combined},  "
                        f"{counts[third]} − {combined} = {counts[third] - combined}",
                    )
                )
    total = sum(counts)
    for left_out in range(4):
        others = [counts[i] for i in range(4) if i != left_out]
        candidates.append(
            (
                "not",
                (left_out, left_out, left_out),
                total - counts[left_out],
                " + ".join(map(str, others)) + f" = {total - counts[left_out]}",
            )
        )
    candidates.append(("all", (0, 0, 0), total, " + ".join(map(str, counts)) + f" = {total}"))
    # pick the kind first so "combo" questions (many ways to fit) don't crowd out the others
    kind = rng.choice(sorted({candidate[0] for candidate in candidates}))
    _, (first, second, third), answer, work = rng.choice(
        [candidate for candidate in candidates if candidate[0] == kind]
    )
    text = TWO_STEP[topic["kind"]][kind].format(
        first=names[first], second=names[second], third=names[third], **topic
    )
    return {"text": text, "answer": answer, "work": work}


# ------------------------------------------------------------------ data sets
def _number_list_dataset(rng, decks):
    """Numerical data: a scrambled list of 12-26 numbers (9-20 coins) for a dot plot,
    at most 8 X's on any one number and some number with at least 3."""
    if not decks.get("number_topics"):
        decks["number_topics"] = rng.sample(NUMBER_TOPICS, len(NUMBER_TOPICS))
    topic = decks["number_topics"].pop()
    if "possible_values" in topic:  # fixed choices (coins): all of them used
        ticks, possible_values = list(topic["ticks"]), list(topic["possible_values"])
        while True:
            counts_per_value = [rng.randint(1, 8) for _ in possible_values]
            if 9 <= sum(counts_per_value) <= 20 and max(counts_per_value) >= 3:
                break
        counts = [
            counts_per_value[possible_values.index(tick)] if tick in possible_values else 0
            for tick in ticks
        ]
    else:  # a window of the topic's range
        all_ticks = list(range(topic["low"], topic["high"] + 1, topic["step"]))
        tick_count = rng.randint(MIN_TICKS, min(MAX_TICKS, len(all_ticks)))
        start = rng.randint(0, len(all_ticks) - tick_count)
        ticks = possible_values = all_ticks[start : start + tick_count]
        min_used = (
            tick_count - 1 if tick_count <= 7 else tick_count // 2 + 1
        )  # short lines: one gap at most
        while True:  # a hump plus some spread, data near both ends
            total, peak = rng.randint(12, 26), rng.uniform(0, tick_count - 1)
            counts = [0] * tick_count
            for _ in range(total):
                index = (
                    round(rng.triangular(-0.5, tick_count - 0.5, peak))
                    if rng.random() < 0.6
                    else rng.randrange(tick_count)
                )
                counts[min(tick_count - 1, max(0, index))] += 1
            if (
                3 <= max(counts) <= 8
                and sum(1 for count in counts if count) >= min_used
                and (counts[0] or counts[1])
                and (counts[-1] or counts[-2])
            ):
                break
    scrambled = [tick for tick, count in zip(ticks, counts) for _ in range(count)]
    rng.shuffle(scrambled)
    return {
        "kind": "numbers",
        "topic": topic,
        "labels": [str(tick) for tick in ticks],
        "ticks": ticks,
        "possible_values": possible_values,
        "counts": counts,
        "scrambled_values": scrambled,
        "scale": 1,
        "list_style": rng.choice(LIST_STYLES),
        "unit": topic["unit"],
        "unit_singular": topic["unit_singular"],
        "given_model": "list",
        "target_model": "number_line",
        "text": topic["intro"].format(name=rng.choice(wp.NAMES)),
    }


def make_dataset(rng, given_model, target_model, decks):
    """One data set for a (given, target) model pair: 4 categories, or a list of
    numbers for list -> dot plot. decks holds per-sheet topic/scale decks, refilled
    when empty, so a sheet doesn't repeat them."""
    if given_model == "list":
        return _number_list_dataset(rng, decks)
    if not decks.get("topics"):
        decks["topics"] = rng.sample(TOPICS, len(TOPICS))
    if not decks.get("scales"):
        decks["scales"] = rng.sample([2, 5, 10], 3)
    topic = decks["topics"].pop()
    scale = 2 if "dot_plot" in (given_model, target_model) else decks["scales"].pop()
    if topic["kind"] == "survey":
        question_names = rng.sample(topic["categories"], 4)  # "apples" in questions
        labels = [name.capitalize() for name in question_names]  # "Apples" on the graphs
        asker = rng.choice(wp.NAMES)
        intro = (
            f"{asker} asked some students to name their favorite {topic['favorite']}. "
            f"The {MODEL_NAME[given_model]} shows the results."
        )
        unit, unit_singular = "students", "student"
    else:
        question_names = labels = rng.sample(wp.NAMES, 4)
        intro = (
            f"{topic['intro']} The {MODEL_NAME[given_model]} shows how many {topic['unit']} "
            f"each friend {topic['verb_past']}."
        )
        unit, unit_singular = topic["unit"], topic["unit_singular"]
    return {
        "kind": "categories",
        "topic": topic,
        "question_names": question_names,
        "labels": labels,
        "unit": unit,
        "unit_singular": unit_singular,
        "counts": _category_counts(rng, given_model, target_model, scale),
        "scale": scale,
        "given_model": given_model,
        "target_model": target_model,
        "text": intro,
    }


def data_summary(dataset, indexes=None):
    """Answer-key text for the data: 'Apples: 12', or '3 at 20' on a number line
    (numbers with no X's left out)."""
    indexes = range(len(dataset["labels"])) if indexes is None else indexes
    labels, counts = dataset["labels"], dataset["counts"]
    if dataset["kind"] == "numbers":
        return ",  ".join(f"{counts[i]} at {labels[i]}" for i in indexes if counts[i])
    return ",  ".join(f"{labels[i]}: {counts[i]}" for i in indexes)


def build_problems(rng, n, list_style="mix"):
    decks, problems = {}, []
    for given_model, target_model in model_pairs(rng, n):
        dataset = make_dataset(rng, given_model, target_model, decks)
        if given_model == "list" and list_style != "mix":
            dataset["list_style"] = list_style
        # from a list the student makes the whole dot plot; otherwise fills in 2 of 4
        dataset["blank"] = (
            set(range(len(dataset["labels"])))
            if given_model == "list"
            else set(rng.sample(range(4), 2))
        )
        dataset["questions"] = [_one_step_question(rng, dataset), _two_step_question(rng, dataset)]
        problems.append(dataset)
    return problems


# -------------------------------------------------------------------- drawing
# Each draw_* takes (canvas, x, y_top, width, height, dataset, blank), where blank
# is the set of category indexes to leave empty for the student to fill in.
def _draw_title(c, x, y_top, w, dataset):
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x + w / 2, y_top - 10, dataset["topic"]["title"])


def _set_font_to_fit(c, text, font, size, max_w, smallest=6):
    while size > smallest and c.stringWidth(text, font, size) > max_w:
        size -= 0.5
    c.setFont(font, size)


def draw_star(c, center_x, center_y, radius, half=False):
    points = []
    for k in range(10):
        angle = math.pi / 2 + k * math.pi / 5
        point_radius = radius if k % 2 == 0 else radius * 0.45
        points.append(
            (center_x + point_radius * math.cos(angle), center_y + point_radius * math.sin(angle))
        )
    c.saveState()
    if half:  # keep the left half only
        clip = c.beginPath()
        clip.rect(center_x - radius - 1, center_y - radius - 1, radius + 1, 2 * radius + 2)
        c.clipPath(clip, stroke=0, fill=0)
    star = c.beginPath()
    star.moveTo(*points[0])
    for point in points[1:]:
        star.lineTo(*point)
    star.close()
    c.setFillColor(STAR)
    c.drawPath(star, stroke=0, fill=1)
    c.restoreState()


def draw_table(c, x, y_top, w, h, dataset, blank):
    _draw_title(c, x, y_top, w, dataset)
    table_w = min(w, 200)
    table_x = x + (w - table_w) / 2
    name_col_w = table_w * 0.45
    row_h = min(20, (h - 18) / 5)
    top = y_top - 16
    c.setFillColor(HEAD_FILL)
    c.rect(table_x, top - row_h, table_w, row_h, stroke=0, fill=1)
    c.setFillColor(black)
    category_header = dataset["topic"]["category_header"]
    _set_font_to_fit(c, category_header, "Helvetica-Bold", 9, name_col_w - 6)
    c.drawCentredString(table_x + name_col_w / 2, top - row_h / 2 - 3, category_header)
    count_header = f"Number of {dataset['unit'].capitalize()}"
    count_col_center = table_x + name_col_w + (table_w - name_col_w) / 2
    _set_font_to_fit(c, count_header, "Helvetica-Bold", 9, table_w - name_col_w - 6)
    c.drawCentredString(count_col_center, top - row_h / 2 - 3, count_header)
    for row, (label, count) in enumerate(zip(dataset["labels"], dataset["counts"]), 1):
        text_y = top - row * row_h - row_h / 2 - 3
        _set_font_to_fit(c, label, "Helvetica", 10, name_col_w - 6)
        c.drawCentredString(table_x + name_col_w / 2, text_y, label)
        if row - 1 not in blank:
            c.setFont("Helvetica", 10)
            c.drawCentredString(count_col_center, text_y, str(count))
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.rect(table_x, top - 5 * row_h, table_w, 5 * row_h, stroke=1, fill=0)
    c.line(table_x + name_col_w, top, table_x + name_col_w, top - 5 * row_h)
    for row in range(1, 5):
        c.line(table_x, top - row * row_h, table_x + table_w, top - row * row_h)


def draw_pictograph(c, x, y_top, w, h, dataset, blank):
    _draw_title(c, x, y_top, w, dataset)
    scale = dataset["scale"]
    label_col_w = 66
    top = y_top - 16
    row_h = min(24, (h - 16 - 20) / 4)
    star_radius = min(7, (row_h - 6) / 2)
    star_step = 2 * star_radius + 3
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.rect(x, top - 4 * row_h, w, 4 * row_h, stroke=1, fill=0)
    c.line(x + label_col_w, top, x + label_col_w, top - 4 * row_h)
    for row, (label, count) in enumerate(zip(dataset["labels"], dataset["counts"])):
        row_top = top - row * row_h
        if row:
            c.setStrokeColor(GRID)
            c.line(x, row_top, x + w, row_top)
        c.setFillColor(black)
        _set_font_to_fit(c, label, "Helvetica", 10, label_col_w - 8)
        c.drawString(x + 5, row_top - row_h / 2 - 3.5, label)
        if row in blank:
            continue
        full_stars, remainder = divmod(count, scale)
        for star in range(full_stars + (1 if remainder else 0)):
            draw_star(
                c,
                x + label_col_w + 6 + star_radius + star * star_step,
                row_top - row_h / 2,
                star_radius,
                half=(star == full_stars),
            )
    key_y = top - 4 * row_h - 13
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    key_text = f"= {scale} {dataset['unit_singular'] if scale == 1 else dataset['unit']}"
    key_w = 26 + 2 * star_radius + 4 + c.stringWidth(key_text, "Helvetica-Bold", 9)
    key_x = x + (w - key_w) / 2
    c.drawString(key_x, key_y, "Key:")
    draw_star(c, key_x + 26 + star_radius, key_y + 3, star_radius)
    c.setFillColor(black)
    c.drawString(key_x + 26 + 2 * star_radius + 4, key_y, key_text)


def draw_bar_graph(c, x, y_top, w, h, dataset, blank):
    _draw_title(c, x, y_top, w, dataset)
    scale = dataset["scale"]
    axis_max = (max(dataset["counts"]) // scale + 1) * scale
    left, right = x + 36, x + w - 4
    bottom, top = y_top - h + 16, y_top - 20
    y_for = lambda value: bottom + (top - bottom) * value / axis_max
    interval_count = axis_max // scale
    label_every = 1 if (top - bottom) / interval_count >= 9 else 2
    c.setLineWidth(0.6)
    for i in range(interval_count + 1):
        value = i * scale
        c.setStrokeColor(GRID)
        c.line(left, y_for(value), right, y_for(value))
        if i % label_every == 0:
            c.setFillColor(black)
            c.setFont("Helvetica", 7)
            c.drawRightString(left - 3, y_for(value) - 2.5, str(value))
    slot = (right - left) / 4
    for i, (label, count) in enumerate(zip(dataset["labels"], dataset["counts"])):
        bar_center = left + slot * (i + 0.5)
        if i not in blank:
            c.setStrokeColor(LINE)
            c.setFillColor(BAR_FILL)
            c.setLineWidth(1)
            c.rect(
                bar_center - slot * 0.3, bottom, slot * 0.6, y_for(count) - bottom, stroke=1, fill=1
            )
        c.setFillColor(black)
        _set_font_to_fit(c, label, "Helvetica", 8, slot - 2)
        c.drawCentredString(bar_center, bottom - 10, label)
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(left, bottom, right, bottom)
    c.line(left, bottom, left, top)
    c.saveState()
    c.translate(x + 7, (bottom + top) / 2)
    c.rotate(90)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(0, 0, f"Number of {dataset['unit'].capitalize()}")
    c.restoreState()


def draw_dot_plot(c, x, y_top, w, h, dataset, blank):
    """Category dot plot: a column of X's above each category name."""
    _draw_title(c, x, y_top, w, dataset)
    c.setFillColor(GRAY)
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(x + w / 2, y_top - 21, f"Each X = 1 {dataset['unit_singular']}")
    left, right = x + 6, x + w - 6
    baseline = y_top - h + 16
    x_mark_step = min(10.5, (h - 16 - 36) / 10)  # 10 Xs stay clear of the key line
    slot = (right - left) / 4
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(left, baseline, right, baseline)
    for i, (label, count) in enumerate(zip(dataset["labels"], dataset["counts"])):
        column_x = left + slot * (i + 0.5)
        c.setStrokeColor(LINE)
        c.line(column_x, baseline - 3, column_x, baseline + 3)
        c.setFillColor(black)
        _set_font_to_fit(c, label, "Helvetica", 8, slot - 2)
        c.drawCentredString(column_x, baseline - 11, label)
        if i in blank:
            continue
        c.setFillColor(STAR)
        c.setFont("Helvetica-Bold", 9)
        for mark in range(count):
            c.drawCentredString(column_x, baseline + 3 + mark * x_mark_step, "X")


def draw_list(c, x, y_top, w, h, dataset, blank):
    """The scrambled numbers in a grid of boxes (easy to cross off while counting)
    or as a plain comma-separated list in a box, per dataset["list_style"]."""
    _draw_title(c, x, y_top, w, dataset)
    numbers = dataset["scrambled_values"]
    top = y_top - 18
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.setFillColor(black)
    c.setFont("Helvetica", 11)
    if dataset["list_style"] == "commas":
        lines = wp.wrap(c, ", ".join(map(str, numbers)), "Helvetica", 11, w - 16)
        c.roundRect(x, top - len(lines) * 16 - 8, w, len(lines) * 16 + 8, 4, stroke=1, fill=0)
        for i, line in enumerate(lines):
            c.drawString(x + 8, top - 16 - i * 16, line)
        return
    columns = min(8, len(numbers), int((w - 4) // 26))
    cell_w, cell_h = 26, 20
    grid_x = x + (w - columns * cell_w) / 2
    for i, number in enumerate(numbers):
        row, column = divmod(i, columns)
        c.rect(grid_x + column * cell_w, top - (row + 1) * cell_h, cell_w, cell_h, stroke=1, fill=0)
        c.drawCentredString(
            grid_x + column * cell_w + cell_w / 2, top - row * cell_h - cell_h / 2 - 4, str(number)
        )


def draw_number_line_dot_plot(c, x, y_top, w, h, dataset, blank):
    """Dot plot on a number line: a tick for every number, even ones with no X's.
    Crowded lines label every other tick (the even multiples of the step)."""
    _draw_title(c, x, y_top, w, dataset)
    c.setFillColor(GRAY)
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(x + w / 2, y_top - 21, f"Each X = 1 {dataset['unit_singular']}")
    left, right = x + 6, x + w - 6
    baseline = y_top - h + 30  # room for tick labels + axis title
    ticks = dataset["ticks"]
    tick_gap = (right - left - 28) / (len(ticks) - 1)
    tick_step = ticks[1] - ticks[0]
    is_labeled = lambda i: tick_gap >= 13 or (ticks[i] // tick_step) % 2 == 0
    x_for = lambda i: left + 14 + tick_gap * i
    x_mark_step = min(10.5, (h - 30 - 30) / 10)  # 10 Xs stay clear of the key line
    c.setStrokeColor(LINE)
    c.setFillColor(LINE)
    c.setLineWidth(1)
    c.line(left, baseline, right, baseline)
    for tip, direction in ((left, 1), (right, -1)):  # arrows at both ends
        arrow = c.beginPath()
        arrow.moveTo(tip, baseline)
        arrow.lineTo(tip + 5 * direction, baseline + 3)
        arrow.lineTo(tip + 5 * direction, baseline - 3)
        arrow.close()
        c.drawPath(arrow, fill=1, stroke=0)
    for i, (label, count) in enumerate(zip(dataset["labels"], dataset["counts"])):
        tick_half = 4 if is_labeled(i) else 2.5
        c.setStrokeColor(LINE)
        c.line(x_for(i), baseline - tick_half, x_for(i), baseline + tick_half)
        if is_labeled(i):
            c.setFillColor(black)
            c.setFont("Helvetica", 9)
            c.drawCentredString(x_for(i), baseline - 13, label)
        if i in blank:
            continue
        c.setFillColor(STAR)
        c.setFont("Helvetica-Bold", 9)
        for mark in range(count):
            c.drawCentredString(x_for(i), baseline + 5 + mark * x_mark_step, "X")
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString((left + right) / 2, baseline - 25, dataset["topic"]["axis_title"])


DRAW_MODEL = {
    "table": draw_table,
    "pictograph": draw_pictograph,
    "bar_graph": draw_bar_graph,
    "dot_plot": draw_dot_plot,
    "list": draw_list,
    "number_line": draw_number_line_dot_plot,
}


# ----------------------------------------------------------------- rendering
QUESTION_TEXT_W = wp.CONTENT_W - wp.TEXT_INDENT - 18 - 128  # room for the answer box


def _block_height(c, dataset):
    intro_lines = len(wp.wrap(c, dataset["text"], "Helvetica", 12, wp.CONTENT_W - wp.TEXT_INDENT))
    questions_h = sum(
        max(2, len(wp.wrap(c, question["text"], "Helvetica", 11, QUESTION_TEXT_W))) * 14 + 8
        for question in dataset["questions"]
    )
    return intro_lines * 15 + 18 + PANEL_H + 8 + questions_h + 12


def draw_question(c, st, part, text):
    x = wp.LMARGIN + wp.TEXT_INDENT
    lines = wp.wrap(c, text, "Helvetica", 11, QUESTION_TEXT_W)
    y = st["y"] - 14
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, f"{part}.")
    c.setFont("Helvetica", 11)
    for i, line in enumerate(lines):
        c.drawString(x + 18, y - i * 14, line)
    box_x = wp.PAGE_W - wp.RMARGIN - 74
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(box_x - 6, y, "Answer:")
    c.setStrokeColor(HexColor("#4a5568"))
    c.setLineWidth(1)
    c.roundRect(box_x, y - 7, 74, 22, 4, stroke=1, fill=0)
    st["y"] -= max(2, len(lines)) * 14 + 8


def render(problems, path, title, label, teks, seed):
    c = canvas.Canvas(path, pagesize=letter)
    c.setTitle(f"{title} — {label}")
    c.setSubject(teks)
    c.setCreator("TEKS worksheet generator")
    st = {"y": 0.0, "page": 1, "show_seed": False}  # seed only on the answer key
    footer, new_page, ensure = wp.make_page(c, st, label, teks, seed)
    wp.draw_header(
        c,
        st,
        title,
        label,
        "Read the data. Complete the second graph or table, then solve the problems.",
    )

    x = wp.LMARGIN + wp.TEXT_INDENT
    half_w = (wp.CONTENT_W - wp.TEXT_INDENT - 16) / 2
    for number, dataset in enumerate(problems, 1):
        given_model, target_model = dataset["given_model"], dataset["target_model"]
        ensure(_block_height(c, dataset))
        wp.draw_problem_text(c, st, number, dataset, None)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, st["y"] - 12, "a.")
        c.setFont("Helvetica", 11)
        task = f"Use the {MODEL_NAME[given_model]} to complete the {MODEL_NAME[target_model]}."
        if given_model == "list":
            task += " Draw one X for each number in the list."
        c.drawString(x + 18, st["y"] - 12, task)
        st["y"] -= 20
        given_w = 180 if given_model == "list" else half_w  # number line gets room to draw X's
        target_w = wp.CONTENT_W - wp.TEXT_INDENT - 16 - given_w
        DRAW_MODEL[given_model](c, x, st["y"], given_w, PANEL_H, dataset, set())
        DRAW_MODEL[target_model](
            c, x + given_w + 16, st["y"], target_w, PANEL_H, dataset, dataset["blank"]
        )
        st["y"] -= PANEL_H + 8
        for part, question in zip("bc", dataset["questions"]):
            draw_question(c, st, part, question["text"])
        st["y"] -= 12

    new_page()
    st["show_seed"] = True
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(wp.LMARGIN, st["y"], f"Answer Key — {label}")
    st["y"] -= 28
    key_text_w = wp.CONTENT_W - wp.TEXT_INDENT
    for number, dataset in enumerate(problems, 1):
        target_name = MODEL_NAME[dataset["target_model"]].capitalize()
        rows = [f"a.  {target_name} — {data_summary(dataset, sorted(dataset['blank']))}"]
        rows += [
            f"{part}.  {question['answer']}   ({question['work']})"
            for part, question in zip("bc", dataset["questions"])
        ]
        lines = [line for row in rows for line in wp.wrap(c, row, "Helvetica", 12, key_text_w)]
        ensure(len(lines) * 16 + 12)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(wp.LMARGIN, st["y"], f"{number})")
        c.setFont("Helvetica", 12)
        for line in lines:
            c.drawString(wp.LMARGIN + wp.TEXT_INDENT, st["y"], line)
            st["y"] -= 16
        st["y"] -= 12

    footer()
    c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="data-graph-word-problems.pdf")
    ap.add_argument("--label", default="Sheet A")
    ap.add_argument("--problems", type=int, default=4)
    ap.add_argument("--title", default="Data and Graphs — Read, Complete, Solve")
    ap.add_argument(
        "--list-style",
        choices=["mix", *LIST_STYLES],
        default="mix",
        help="how a list of numbers is shown: grid of boxes, commas, or mix (default)",
    )
    args = ap.parse_args()
    args.out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)  # e.g. --out sheets/A.pdf
    rng = random.Random(args.seed)
    problems = build_problems(rng, args.problems, args.list_style)
    render(problems, args.out, args.title, args.label, "Texas TEKS 3.8(A), 3.8(B)", args.seed)
    print(f"Wrote {args.out}  ({len(problems)} problems + answer key)")


if __name__ == "__main__":
    main()
