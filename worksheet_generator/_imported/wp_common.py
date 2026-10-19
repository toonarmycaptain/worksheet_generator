"""Shared core for the TEKS add/subtract word-problem worksheet generators.

Holds the problem bank + generation, text wrapping, page scaffolding, header,
and answer-key page so each per-representation script (base-ten blocks, strip
diagrams, number lines, ...) only has to draw its own model.

Imported by the generate_*_word_problems.py scripts (same directory).
"""

from __future__ import annotations

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import letter

# ------------------------------------------------------------------ page layout
PAGE_W, PAGE_H = letter
LMARGIN = RMARGIN = TMARGIN = BMARGIN = 54
CONTENT_W = PAGE_W - LMARGIN - RMARGIN
TEXT_INDENT = 22

# ---------------------------------------------------------------- problem bank
NAMES = [
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
]
OBJECTS = [
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
]

ADD_TEMPLATES = [
    "{n1} collected {a} {obj}. {n2} collected {b} {obj}. How many {obj} did they collect altogether?",
    "There were {a} {obj} in the bin. {n1} put in {b} more. How many {obj} are in the bin now?",
    "{n1} had {a} {obj} and found {b} more. How many {obj} does {n1} have now?",
    "{n1} read {a} pages on Monday and {b} pages on Tuesday. How many pages in all?",
    "{n1} scored {a} points, then scored {b} more points. How many points in all?",
    "A basket held {a} {obj}. {n1} added {b} more. How many {obj} are in the basket now?",
]
SUB_TEMPLATES = [
    "{n1} had {a} {obj}. {n1} gave away {b} of them. How many {obj} does {n1} have left?",
    "There were {a} {obj} on the shelf. {b} of them were sold. How many {obj} are left?",
    "{n1} had {a} {obj} and used {b}. How many {obj} are left?",
    "A book has {a} pages. {n1} has read {b} pages. How many pages are left to read?",
    "{n1} had {a} points and lost {b} points. How many points does {n1} have now?",
    "{n1} needs {a} {obj} in all and has {b} so far. How many more {obj} are needed?",
]

PROFILES = [(2, 2), (2, 3), (3, 2), (3, 3)]  # (digits of a, digits of b), cycled + shuffled


def digits(n):
    return n // 100, (n // 10) % 10, n % 10


def place_chunks(n):
    """Split into nonzero place-value parts, e.g. 149 -> [100, 40, 9]."""
    parts = [(n // 100) * 100, (n // 10 % 10) * 10, n % 10]
    return [v for v in parts if v]


def _num(rng, d, hundreds_cap=9):
    if d == 2:
        return rng.randint(11, 99)
    return rng.randint(100, hundreds_cap * 100 + 99)


def build_problems(rng, n, hundreds_cap=9, min_diff=10, add_sorted=False):
    """Balanced add/subtract, mixed 2-/3-digit, no trivial differences.

    add_sorted=True orders addition operands a>=b (keeps a-b>=0, e.g. for
    number-line distractors that reverse the operation).
    """
    profiles = [PROFILES[i % len(PROFILES)] for i in range(n)]
    rng.shuffle(profiles)
    ops = ["add"] * ((n + 1) // 2) + ["sub"] * (n // 2)
    rng.shuffle(ops)
    problems = []
    for (da, db), op in zip(profiles, ops):
        n1, n2 = rng.sample(NAMES, 2)
        obj = rng.choice(OBJECTS)
        if op == "add":
            for _ in range(200):
                a, b = _num(rng, da, hundreds_cap), _num(rng, db, hundreds_cap)
                if a + b <= 999:
                    break
            if add_sorted:
                a, b = max(a, b), min(a, b)
                if a == b:
                    b -= 1  # keep a > b for number-line distractors
            text = rng.choice(ADD_TEMPLATES).format(n1=n1, n2=n2, a=a, b=b, obj=obj)
            answer = a + b
        else:
            for _ in range(200):
                a, b = _num(rng, da, hundreds_cap), _num(rng, db, hundreds_cap)
                a, b = max(a, b), min(a, b)
                if a - b >= min_diff:
                    break
            text = rng.choice(SUB_TEMPLATES).format(n1=n1, n2=n2, a=a, b=b, obj=obj)
            answer = a - b
        problems.append({"op": op, "a": a, "b": b, "answer": answer, "text": text})
    return problems


# ----------------------------------------------------------------- text helper
def wrap(c, text, font, size, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if c.stringWidth(trial, font, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------- page plumbing
def make_page(c, st, label, teks, seed):
    """Return (footer, new_page, ensure) closures over a shared state dict st.

    Set st["show_seed"] = False to leave the seed off the footer (e.g. on
    student pages, turning it back on for the answer key).
    """

    def footer():
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#718096"))
        seed_txt = f"  •  seed {seed}" if st.get("show_seed", True) else ""
        c.drawString(LMARGIN, 30, f"{label}  •  {teks}{seed_txt}")
        c.drawRightString(PAGE_W - RMARGIN, 30, f"Page {st['page']}")

    def new_page():
        footer()
        c.showPage()
        st["page"] += 1
        st["y"] = PAGE_H - TMARGIN

    def ensure(h):
        if st["y"] - h < BMARGIN + 24:
            new_page()

    return footer, new_page, ensure


def draw_header(c, st, title, label, subtitle):
    st["y"] = PAGE_H - TMARGIN
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(LMARGIN, st["y"] - 2, title)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor("#2b6cb0"))
    c.drawRightString(PAGE_W - RMARGIN, st["y"] - 2, label)
    st["y"] -= 18
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#4a5568"))
    c.drawString(LMARGIN, st["y"], subtitle)
    st["y"] -= 16
    c.setFillColor(black)
    c.setFont("Helvetica", 11)
    c.drawString(LMARGIN, st["y"], "Name: ______________________________")
    c.drawRightString(PAGE_W - RMARGIN, st["y"], "Date: ______________")
    st["y"] -= 12
    c.setStrokeColor(HexColor("#cbd5e0"))
    c.setLineWidth(1)
    c.line(LMARGIN, st["y"], PAGE_W - RMARGIN, st["y"])
    st["y"] -= 18


def draw_problem_text(c, st, idx, p, hint):
    """Number + wrapped problem text + a gray hint line. Leaves st['y'] below."""
    lines = wrap(c, p["text"], "Helvetica", 12, CONTENT_W - TEXT_INDENT)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(black)
    c.drawString(LMARGIN, st["y"] - 11, f"{idx})")
    c.setFont("Helvetica", 12)
    for line in lines:
        c.drawString(LMARGIN + TEXT_INDENT, st["y"] - 11, line)
        st["y"] -= 15
    if hint:
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(HexColor("#718096"))
        c.drawString(LMARGIN + TEXT_INDENT, st["y"] - 10, hint)
        st["y"] -= 16
    return len(lines)


def draw_answer_row(c, st):
    ya = st["y"] - 24
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(black)
    c.drawString(LMARGIN + TEXT_INDENT, ya + 6, "Answer:")
    c.setStrokeColor(HexColor("#4a5568"))
    c.setLineWidth(1)
    c.roundRect(LMARGIN + TEXT_INDENT + 56, ya, 74, 22, 4, stroke=1, fill=0)
    st["y"] = ya - 18


def answer_key_page(c, st, new_page, label, problems):
    new_page()
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(LMARGIN, st["y"], f"Answer Key — {label}")
    st["y"] -= 28
    c.setFont("Helvetica", 12)
    for i, p in enumerate(problems, 1):
        sign = "+" if p["op"] == "add" else "−"
        c.drawString(LMARGIN, st["y"], f"{i})  {p['a']} {sign} {p['b']} = {p['answer']}")
        st["y"] -= 20
