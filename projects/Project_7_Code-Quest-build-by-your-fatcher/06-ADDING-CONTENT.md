---
layout: default
title: Phase 6 Adding or changing content
parent: 9. Code-Quest-build-by-your-fatcher
nav_order: 6
---

# 06 · Adding or changing content

All lessons are plain Python data. No database, no build step. Restart the server (or `docker compose up --build`) after a change.

## Which file for which lesson

| You want to change | Edit |
|---|---|
| A small Beginner lesson | `lessons_b1.py`, `lessons_b2.py`, `lessons_b3.py` |
| A small Intermediate or Expert lesson | `lessons_adv1.py`, `lessons_adv2.py`, `lessons_adv3.py` |
| A main path lesson | `lessons_path.py` |
| A Story Project | `lessons.py` (C++, Java and syntax parts in `lessons_extra.py`) |
| A Tool Track lesson | `lessons_tools.py` |
| A Mini Project | `lessons_mini.py` |
| Real-world stories | `stories.py` (feeds, filters, fallback stories) |
| Syntax note wording | `lessons_syntax.py` |
| The welcome message | `welcome()` in `index.html` |
| The mascot | the `<svg>` inside `<div id="mascot">` in `index.html` |

## Add a small Beginner lesson (`B`)

Use one C-style body for C#, C++ and Java. `OUT(...)` prints a line, and `STR`/`BOOL` are replaced with the right type.

```python
a(B(6, "games", "Double the Score",
    "Multiply to double a number.",
    "Double a score and print it.",
    ["score * 2 doubles it.", "The result is printed."],
    r'''score = 50
print(score * 2)
''',
    cf=r'''int score = 50;
OUT(score * 2);'''))
```

The first number is the topic index (0 to 9). Use `x=(cs, cpp, java)` instead of `cf=` when the languages differ.

## Add a small Intermediate or Expert lesson (`A`)

Each language gets its own code. `cpre` holds C++ code before `main`; `jextra` holds Java methods inside `Main`; `jafter` holds extra Java classes.

```python
a(A(13, "games", "Double It",
    "A function can return a number.",
    "Write a function that doubles a number.",
    ["The function returns n * 2."],
    r'''def twice(n):
    return n * 2
print(twice(21))''',
    r'''Console.WriteLine(Twice(21));
int Twice(int n) => n * 2;''',
    r'''cout << twice(21) << endl;''',
    r'''System.out.println(twice(21));''',
    cpre='int twice(int n) { return n * 2; }',
    jextra='static int twice(int n) { return n * 2; }'))
```

The first number is the main lesson (11 to 24) that it belongs under.

## Add a Tool Track lesson (`T`)

```python
T("t_bl9", "blender", 2, "Blender: your title",
  "The idea in one or two sentences.",
  'print("practice code that runs in Code Quest")\n',
  'import bpy\n# the real script to paste into Blender',
  ["Explain line 1.", "Explain line 2."],
  "A tip.", "A remix challenge.", "A short story.", "A note about versions.")
```

Valid apps: `blender`, `maya`, `houdini`, `houdini_py`, `unity`, `unreal`. Unity practice code is C# and Unreal practice code is C++; the others are Python.

## Add a Mini Project (`M`)

```python
M("m_new", "App name", "🟢", "games", 2, "Title",
  "One-line concept", "Goal", ["prerequisite lesson titles"],
  [dict(title="Step", text="What to do", code="...", check="What you should see")],
  "Share idea", "Pro tip", "Remix idea")
```

## Checking your work

Run the lesson in all languages and compare the output. The project includes the pattern used during the build: run each lesson's Python, C++ and Java versions and check the outputs match exactly (see [Quality](08-QUALITY-AND-LIMITS.md)).

## Teach the syntax generator a new pattern

In `lessons_syntax.py`, add a row to the list for the language:

```python
("keyname", r"\bregex\b", "One simple sentence."),
```

Rows are checked in order, so put more specific patterns first. Up to three notes are shown per lesson.

## Tips for writing good lessons

- One idea per lesson, 5–15 minutes.
- Print something the learner can see change when he edits a number.
- Use plain words in `explain`. Avoid jargon without a short definition.
- Keep output identical across languages (watch decimal formatting and evaluation order).
- Write the task so any of the four interests can fit.
