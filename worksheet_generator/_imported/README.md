# Math Worksheet Generators (Texas TEKS, Grade 2–3)

These tools make printable math worksheets as PDF files, ready to print or share.
Each worksheet uses a different picture model (base-ten blocks, strip diagrams, number
lines, arrays, …). Most also come with an answer key on the last page.

Every worksheet is built from a **seed number**. The same seed always gives exactly the
same worksheet. A different seed gives a new set of numbers. That makes it easy to make
Sheet A, Sheet B, a retake, and so on, and to print the same sheet again later.

---

## Part 1 — Guide for teachers (no programming needed)

### What you need (one-time setup)

1. **A program called `uv`.** It runs these tools and fetches everything else they need
   automatically. To install it, open the **Terminal** app, paste the line below, and
   press Enter:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Then close the Terminal and open it again.
2. **This folder** (`base-ten-worksheets`) saved on your computer. The instructions
   below assume it is in your `Documents` folder.

### Make a worksheet in three steps

1. Open the **Terminal** app.
2. Go to this folder. Paste this and press Enter:

   ```bash
   cd ~/Documents/base-ten-worksheets
   ```

3. Paste one of the commands from the list below and press Enter. After a few seconds
   you'll see a line like `Wrote mult-A.pdf (4 problems + answer key)`, and the PDF
   will be in this folder.

> **Tip:** Run the commands from this folder (step 2). If you see an error like
> `can't open file '…generate_….py': No such file or directory`, you probably skipped step 2.

### The worksheets

| Worksheet | What students do | Command to paste |
|---|---|---|
| **Base-ten block word problems** | Solve add/subtract word problems with pictures of base-ten blocks | `uv run --with reportlab python generate_block_word_problems.py --seed 31 --out blocks-A.pdf` |
| **Strip diagram word problems** | Solve add/subtract word problems with a part-part-whole strip diagram | `uv run --with reportlab python generate_strip_word_problems.py --seed 201 --answer-key --out strip-A.pdf` |
| **Number line, multiple choice** | Pick which of 4 number lines shows how to solve the problem | `uv run --with reportlab python generate_number_line_mc_word_problems.py --seed 301 --out numberline-mc-A.pdf` |
| **Number line, fill in** | Fill in the jumps on a number line to solve the problem | `uv run --with reportlab python generate_number_line_word_problems.py --seed 401 --out numberline-A.pdf` |
| **Multiplication, pick the models** | Read a multiplication story and circle the **3** pictures (out of 6) that match it | `uv run --with reportlab python generate_multiplication_mc_word_problems.py --seed 501 --out mult-A.pdf` |
| **Data and graphs** | Read a table or graph, complete a different graph of the same data, then solve a one-step and a two-step problem | `uv run --with reportlab python generate_data_graph_word_problems.py --seed 801 --out data-A.pdf` |
| **Data and graphs, multiple choice** | See data shown one way and pick which of 4 graphs or tables (A–D) shows the same data | `uv run --with reportlab python generate_data_graph_mc_word_problems.py --seed 901 --out data-mc-A.pdf` |
| **Word problems, text only** | Solve add/subtract word problems with no picture | `uv run --with reportlab python generate_word_problems.py --seed 601 --out words-A.pdf` |
| **Base-ten block practice** | Not word problems: write the number shown, then add and subtract with blocks | `uv run --with reportlab python generate_worksheet.py --seed 701 --out practice-A.pdf` |

### Changing a worksheet

Add any of these to the end of a command (before pressing Enter):

| To… | Add this | Example |
|---|---|---|
| Get different numbers | `--seed` and any whole number | `--seed 42` |
| Name the file (and choose a folder) | `--out` and a file name ending in `.pdf`. You can put it in a folder; the folder is created if it doesn't exist yet | `--out tuesday.pdf` or `--out week-3/tuesday.pdf` |
| Change the label in the top-right corner | `--label` and text in quotes | `--label "Day 2 · Sheet B"` |
| Change the number of problems | `--problems` and a number | `--problems 6` |
| Change the big title | `--title` and text in quotes | `--title "Warm-Up"` |

These work for every worksheet except **Base-ten block practice**, which has its own
options (see the [technical reference](#generate_worksheetpy-base-ten-computation-practice-different-options)).
The **strip diagram** worksheet only includes an answer key if you add `--answer-key`.

**Example:** two different multiplication sheets for the same day:

```bash
uv run --with reportlab python generate_multiplication_mc_word_problems.py --seed 501 --label "Sheet A" --out mult-A.pdf
uv run --with reportlab python generate_multiplication_mc_word_problems.py --seed 502 --label "Sheet B" --out mult-B.pdf
```

### About the multiplication worksheet (TEKS 3.4(K))

Each problem is a short story about equal groups, for example *"A frog hops 4 spaces each
time it jumps. It jumps 7 times. How many spaces does the frog move in all?"* Below it
are **6 pictures, labeled A–F**. Students circle the **3** that show the story.

- **The four kinds of picture** are an **array** of dots, a **number line** with equal
  jumps, a **tape (strip) diagram**, and **repeated addition** (`4 + 4 + 4 + … = ?`).
- **The 3 correct pictures are always 3 different kinds.** A kind can appear twice, but
  only one of the two will be correct. All four kinds appear in every problem.
- **The answer is never shown.** The total is always a `?`, so students can't spot the
  wrong pictures just by comparing totals.
- **Arrays may be turned sideways.** For 7 groups of 4, an array of 4 rows of 7 also
  counts as correct. The other pictures always match the story exactly (7 groups of 4,
  never 4 groups of 7).
- **Number line jumps are numbered** 1, 2, 3, … so students can count the jumps. For a
  harder sheet, add `--no-jump-labels` to the command: the jumps are drawn without
  numbers, and students count them themselves.
- **Wrong pictures are common mistakes, and they never use a number that isn't in the
  story.** For a story about 4 groups of 9, a wrong picture might show 4 groups of 4,
  9 groups of 9, `4 + 9`, or one group too many. It would never show 8s or 10s, which
  would make it too easy to rule out.
- **Numbers:** both numbers are between 2 and 12, and the total is never more than 100.
- **The answer key** (last page) lists the 3 correct letters and the multiplication
  fact for each problem, plus a short reason each wrong picture doesn't match.

### About the data and graphs worksheet (TEKS 3.8(A), 3.8(B))

Each problem is one set of data with 4 categories, for example a survey (*"Hana asked
some students to name their favorite lunch"*) or four friends keeping track of something
(cans collected, books read, points scored, tickets sold). Students do three things:

- **a. Complete a model (3.8(A)).** The data is shown one way, and students use it to
  fill in 2 blank categories in a *different* model of the same data.
- **b. A one-step problem (3.8(B)):** how many more, how many fewer, or how many in all
  for two categories.
- **c. A two-step problem (3.8(B)):** for example *"How many more students chose pasta or
  salad than chose tacos?"*, *"How many students did NOT choose soup?"*, or the total.

Good to know:

- **The four models** are a **frequency table**, a **pictograph** (with a key like
  *each star = 5 students*), a **bar graph** with scaled intervals, and a **dot plot**.
  On a 4-problem sheet each model is the one to complete exactly once.
- **One problem per sheet starts from a list of numbers** instead of a model, for
  example the number of students in each class at a school, or the value of each coin in
  a piggy bank in cents. The numbers are scrambled, and students make the whole dot plot
  on a number line, drawing one X for each number. The number line has 6 to 18 values
  (for example 11 to 27), and values that nobody has are still marked on it. Questions
  b and c ask things like *"How many classes have 20 or 21 students?"* or *"How many
  games had 14 or more points?"*
- **The list can be a grid of boxes** (easy to cross off while counting) **or a
  comma-separated list** (*12, 20, 17, 19, …*). By default each sheet picks one; add
  `--list-style grid` or `--list-style commas` to choose.
- **Scales are 2, 5 or 10.** A pictograph may use a half star (half of the key), and a
  bar may end halfway between two lines. Dot plots always count by 1, so they stay
  small (10 or fewer per category).
- **No ties.** The 4 counts are always different numbers.
- **The answer key** (last page) lists the missing values for part a, and the answer
  and number sentence for parts b and c.

**Multiple-choice version (3.8(A)).** Each problem shows the data one way, for example a
pictograph, and asks *"Which bar graph shows the same data?"*. The 4 choices (A–D) are all
the same kind of model. One is correct, and the 3 wrong ones are common mistakes:

- two categories **switched**,
- one category **off** by one step of the scale, or by half a step (a bar ending on a
  line instead of between two lines, a whole star instead of a half star),
- the right picture with the **wrong scale**: the key says each star = 10 instead of 5,
  the bar graph counts by 10 instead of 5, or a table lists the number of stars instead of
  the number of students.

The list-of-numbers problem asks *"Which dot plot shows the same data?"*. Its wrong dot
plots are counting mistakes: one number miscounted by 1, the X's for two numbers
switched, only one X for each number that appears, or every X one place over.

There is one problem per page, so the graphs are big enough to read. The answer key gives
the correct letter and the data, plus why each wrong choice doesn't match.

### Good to know

- **Use a different seed for each sheet.** The strip diagram and number line worksheets
  share their story problems, so the same seed gives the same numbers drawn a different
  way. That's handy if you *want* to show one problem with several models.
- **The seed is printed at the bottom of the answer key** for the multiplication and
  both data and graphs worksheets, so you can make the exact same sheet again later. On the other worksheets
  it is currently printed at the bottom of every page.
- **Running a command again with the same `--out` name replaces that file.** Use a new
  name if you want to keep the old one.

---

## Part 2 — Technical reference

### Requirements

- [`uv`](https://docs.astral.sh/uv/) installed. The drawing library (`reportlab`) is
  pulled in automatically by `--with reportlab`, so there's **nothing else to install**.
- Run the commands **from this folder** (`~/Documents/base-ten-worksheets`) so the short
  script names resolve. (Running a script by its full path from elsewhere also works:
  Python finds `wp_common.py` next to the script.)

### Command pattern

```bash
uv run --with reportlab python <script> [options]
```

### The generators

| Script | What it makes | Day | Default # problems | TEKS |
|---|---|---|---|---|
| `generate_block_word_problems.py` | Word problems drawn with **base-ten blocks** (flat/rod/unit) | 1 | 4 (2 per page) | 2.2(A), 3.4(A) |
| `generate_strip_word_problems.py` | Word problems with **strip diagrams** (part-part-whole bar models) | 2 | 4 (1 page) | 3.5(A) |
| `generate_number_line_mc_word_problems.py` | **Multiple-choice number lines**: pick which line shows the solution | 3 | 4 (1 page) | 3.4(A), 3.5(A) |
| `generate_multiplication_mc_word_problems.py` | **Multiplication** word problems with 6 model choices (array / number line / tape diagram / repeated addition): circle the **3 correct** | — | 4 (2 per page) | 3.4(K) |
| `generate_data_graph_word_problems.py` | **Data and graphs**: read a frequency table / pictograph / bar graph / dot plot, complete a different one, solve one- and two-step problems | — | 4 (2 per page) | 3.8(A), 3.8(B) |
| `generate_data_graph_mc_word_problems.py` | **Data and graphs, multiple choice**: pick which of 4 graphs/tables shows the given data | — | 4 (1 per page) | 3.8(A) |
| `generate_word_problems.py` | Word problems, **text only** (no diagram) | — | 6 (1 page) | 3.4(A) |
| `generate_number_line_word_problems.py` | Number line, student **fills in** each jump (alternative to the MC version) | — | 4 (1 page) | 3.4(A), 3.5(A) |
| `generate_worksheet.py` | Base-ten block **computation practice** (not word problems): "write the number", add, subtract | — | 2/2/2 | 2.2(A), 2.4(C) |

`wp_common.py` is a shared module (problem bank, page layout, answer key). The other
scripts import it, and it is **not run directly**.

### Arguments

#### Word-problem generators
(`block`, `strip`, `number_line_mc`, `multiplication_mc`, `data_graph`, `data_graph_mc`, `word_problems`, `number_line`)

| Argument | Default | What it does |
|---|---|---|
| `--seed N` | `1` | Random seed. **Same seed = same problems.** Change it for a new worksheet. |
| `--label "..."` | `"Sheet A"` or `"Day N · Sheet A"` | Text shown top-right and in the footer/answer-key title. |
| `--problems N` | see table | How many problems. Larger counts flow onto extra pages. |
| `--out FILE.pdf` | script-specific | Output filename. |
| `--title "..."` | script-specific | Big title at the top of the sheet. |

`generate_strip_word_problems.py` also takes:

| Argument | Default | What it does |
|---|---|---|
| `--answer-key` | off | Add an answer-key page. Without it, the PDF has no answer key. |

`generate_multiplication_mc_word_problems.py` also takes:

| Argument | Default | What it does |
|---|---|---|
| `--max-factor N` | `12` | Largest factor (both factors are 2..N). |
| `--max-product N` | `100` | Largest product. |
| `--no-jump-labels` | off | Leave the number-line jumps unnumbered (students count the arcs). |

`generate_data_graph_word_problems.py` and `generate_data_graph_mc_word_problems.py` also take:

| Argument | Default | What it does |
|---|---|---|
| `--list-style mix\|grid\|commas` | `mix` | How a list of numbers is shown: a grid of boxes, a comma-separated list, or picked at random for each list problem. |

#### `generate_worksheet.py` (base-ten computation practice, different options)

| Argument | Default | What it does |
|---|---|---|
| `--seed N` | `1` | Random seed. |
| `--represent N` | `2` | Number of "write the number shown by the blocks" problems. |
| `--add N` | `2` | Number of addition problems. |
| `--sub N` | `2` | Number of subtraction problems. |
| `--no-regroup` | off | Avoid problems that require carrying/borrowing. |
| `--bw` | off | Grayscale (toner-friendly) instead of color blocks. |
| `--out FILE.pdf` | `demo.pdf` | Output filename. |
| `--title "..."` | (default title) | Big title at the top. |

### Reproduce the delivered sheets

```bash
# Day 1 — base-ten blocks
uv run --with reportlab python generate_block_word_problems.py       --seed 31  --label "Day 1 · Sheet A" --out block-word-problems-A.pdf
uv run --with reportlab python generate_block_word_problems.py       --seed 74  --label "Day 1 · Sheet B" --out block-word-problems-B.pdf

# Day 2 — strip diagrams
uv run --with reportlab python generate_strip_word_problems.py       --seed 201 --label "Day 2 · Sheet A" --out strip-word-problems-A.pdf
uv run --with reportlab python generate_strip_word_problems.py       --seed 202 --label "Day 2 · Sheet B" --out strip-word-problems-B.pdf

# Day 3 — number lines (multiple choice)
uv run --with reportlab python generate_number_line_mc_word_problems.py --seed 301 --label "Day 3 · Sheet A" --out number-line-mc-A.pdf
uv run --with reportlab python generate_number_line_mc_word_problems.py --seed 302 --label "Day 3 · Sheet B" --out number-line-mc-B.pdf
```

### Make a whole week at once

```bash
for i in 1 2 3 4 5; do
  uv run --with reportlab python generate_strip_word_problems.py \
    --seed $((200 + i)) --label "Day 2 · Set $i" --out "strip-set-$i.pdf"
done
```

### Implementation notes

- **Output path:** every generator expands `~` in `--out` and creates missing parent
  folders before saving, so `--out sheets/week-3/A.pdf` works even if `sheets/` doesn't
  exist yet.
- **Answer keys:** the answer key is the last page of every PDF except the strip
  generator, which adds one only with `--answer-key`.
- **Seed in the footer:** `wp_common.make_page` prints the seed in the footer unless
  `st["show_seed"]` is `False`. The multiplication and both data/graph generators turn it off for student
  pages and back on for the answer key. The other generators still print it on every page.
- **Add/subtract numbers:** mixed 2- and 3-digit within 1,000, add/subtract balanced per
  sheet, and subtraction differences are always at least 10 (no trivial `37 − 36`).
- **Base-ten block word problems** keep 3-digit numbers to hundreds ≤ 5, so each number
  stays on one readable row of blocks.
- **Number-line multiple choice:** every line starts at 0 and shows both numbers as jumps
  (`0 →+a→ a →±b→ answer`). The three wrong choices are the classic errors: wrong
  operation/direction, wrong result, and a misread second number.
- **Multiplication multiple choice** (story = *g* groups of *s*):
  - **Choices:** 6 (A–F). Exactly 3 are correct, and those 3 are 3 different models. A
    model may repeat, but only one of each model is ever correct, and all four models
    appear in every problem. The total is always `?`.
  - **Flipped forms:** a flipped array (*s* × *g*) counts as correct. The other models
    are never drawn flipped, not as a correct choice and not as a wrong one.
  - **Wrong number lines:** *g* jumps of *g* or *s* jumps of *s*. The jump count always
    equals the jump size, and both come from the story. For square facts (*g* = *s*)
    there's no wrong number line, so the number line is always one of the correct choices.
  - **Wrong tape diagrams and repeated additions:** only numbers from the story. They are
    *g* ± 1 groups of *s*, *g* groups of *g*, *s* groups of *s*, or *g* + *s* (the last
    one isn't used for squares).
  - **Wrong arrays:** *g* ± 1 rows, *s* ± 1 columns, or *g* rows of *g*.
  - **Drawing:** arrays with a side longer than 7 are drawn landscape, as one evenly
    spaced grid. Number-line arcs are labeled with the jump number (1, 2, 3, …), or left
    blank with `--no-jump-labels`. The flag only changes the drawing, so the same seed
    gives the same problems and choices either way.
  - **Numbers:** factors 2–12, product ≤ 100, and 2 × 2 is excluded. No fact (or its
    flip) repeats on one sheet.
- **Data and graphs** (`generate_data_graph_word_problems.py`):
  - **Pairs:** the given models are a shuffle of table / pictograph / bar / dot plot, and
    the model to complete is the same list rotated by 1–3, so a model is never paired with
    itself. The pair that would end in a (categorical) dot plot becomes **list → number-line
    dot plot** instead, so each model is still the one to complete once per 4. More than 4
    problems cycle through the same pairs.
  - **Numerical lists** (`NUMBER_TOPICS`): most topics give a realistic range (`low`,
    `high`, `step`, e.g. class sizes 15–30). Each problem takes a window of 6–18 ticks
    (`MIN_TICKS`, `MAX_TICKS`) from it as the number line. Coins are fixed instead:
    `possible_values` 5, 10, 25 on `ticks` 0–30. The list has 12–26 numbers (9–20
    coins), drawn as a hump plus some spread. Every tick has at most 8 X's, some tick has
    at least 3, and the data reaches near both ends of the line. Short lines (≤ 7 ticks)
    skip at most one value, and longer lines use at least half of them. Questions use
    the topic's `phrase` (*"have {amount}"*, *"are worth {amount}"*): one-step "how many
    more" or "*x* or *y*", two-step "*x* or more / or fewer" or "*x* or *y* vs *z*".
  - **Lists:** `draw_list` shows the scrambled numbers as a grid of boxes or a wrapped
    comma list (`dataset["list_style"]`, chosen per problem, or set by `--list-style`).
    On crowded number lines (ticks < 13 pt apart) only every other tick is labeled. In
    the fill-in sheet the list gets a narrower panel so the dot plot has room for X's.
  - **Counts:** 4 distinct values. With a dot plot in the pair: 1–10 (and scale 2 for
    the other model). Otherwise scale 2, 5 or 10 (no repeat until all three are used),
    counts are multiples of the scale or of half the scale when it's even, up to 8 ×
    scale, so a pictograph row has at most 8 stars.
  - **Part a:** 2 of the 4 categories are blank in the model to complete. From a list,
    the whole dot plot is blank (only the number line is drawn).
  - **Two-step questions:** the kind (combined vs one, one vs combined, "did NOT
    choose", total) is picked first, then a set of categories where the answer is
    positive.
  - Seed is printed only on the answer key, like the multiplication generator.
  - `model_pairs`, `make_dataset`, `data_summary` and the `DRAW_MODEL` functions are
    shared with the MC version. A problem is a `dataset` dict: `given_model` /
    `target_model` (the model to complete or pick), `labels` and `counts`, `scale`,
    `blank` (indexes left for the student), and for number lists `ticks` and
    `scrambled_values`.
- **Data and graphs multiple choice** (`generate_data_graph_mc_word_problems.py`):
  - Imports the data sets and drawing from `generate_data_graph_word_problems.py`, so
    the topics, scales and counts follow the same rules. The choices are drawn as the
    pair's `target_model`.
  - **Wrong choices:** every swap, off-by-a-step (scale step or half step; 1 or 2 for
    dot plots, capped at 10), and wrong-scale variant (same picture, key/axis of 1, 2, 5
    or 10, only when every value stays a whole number) goes into a pool. Three are picked
    with different kinds first, and none looks the same as another choice.
  - **Wrong number-line dot plots** (from a list): ±1 on one value, two values' X's
    swapped, one X per value that appears, or all X's shifted one tick (only when the
    end tick is empty and every tick is a possible value).
  - Options use their own seeded rng (`"{seed}-{idx}"`), like the multiplication MC.
- **To add a new model/day:** copy one of the `generate_*_word_problems.py` scripts,
  `import wp_common as wp`, and change only the drawing code.
- **Plans:** see `TODO.md` for the plan to generalise the generators into shared code
  behind a website, and the cleanup that goes with it.
