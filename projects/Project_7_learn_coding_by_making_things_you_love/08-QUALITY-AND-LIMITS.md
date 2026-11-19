# 08 · Quality and known limits

An honest picture of what has been verified and what still needs checking on a real machine.

## What is verified

| Area | How it was checked | Result |
|---|---|---|
| Beginner small lessons (90) | Python, C++ and Java run; outputs compared | Identical |
| Intermediate and Expert small lessons (50) | Same check | Identical |
| Syntax notes | Every lesson has at least 2 notes per language (Beginner) and at least 1 (others) | ✅ |
| Server API | `/api/lessons` returns all lessons; ids are unique; numbering is continuous | ✅ |
| Tool Track practice code | Python and C++ practice programs run and print the expected output | ✅ |
| Front end in a real browser (headless Chromium) | Opened home, Tool Track, Mini Projects, lessons; ran code in three languages; no page errors | ✅ |
| Stories parser | Tested with sample RSS data (HTML stripped, bad links and blocked words dropped) and the offline fallback | ✅ |

## What is **not** verified yet

| Area | Why | What to do |
|---|---|---|
| **C# versions of the lessons** | The build environment had no `dotnet` | Run the lessons in Docker; report failures |
| **Docker image build** | Not built in the build environment | Run `docker compose up --build` once |
| **Live RSS feeds** | The build environment had no internet | Check that stories show "live"; fix feed URLs in `stories.py` |
| **Blender, Maya, Houdini scripts** | The applications were not installed | Run each lesson in the real application |
| **Unity and Unreal scripts** | Not installed | Same; Unreal C++ must compile in Visual Studio |
| **Mini Projects end to end** | Same | Follow each project once in the real application |
| **iPad use** | Needs a real device | Try `--lan` on the home network |

Scripts follow current documented APIs (Blender 3.x/4.x, Maya 2022+, Houdini 19+, Unity 2022 LTS+, Unreal 5), but software versions change, so expect small fixes.

## Known limits

- **Not safe for public hosting.** It runs learner code on the server. See the [roadmap](09-ROADMAP.md).
- **Progress is per browser.** Clearing browser data or switching browsers loses it. There are no accounts.
- **Unreal C++ is advanced.** The lessons say so and mention Blueprints.
- **Houdini VEX lessons have no generated syntax notes** (the notes engine covers Python, C#, C++ and Java).
- **Newest Blender versions change some APIs.** The keyframe lessons use `keyframe_insert`, which is stable; render engine names were deliberately avoided.
- **Stories depend on third-party feeds.** URLs can move; the app falls back to built-in stories.
- **The old 25 main lessons** were not re-verified in this round of testing; only the 140 small lessons were checked automatically.

## Test script (pattern)

For each lesson, write the Python, C++ and Java code to temp files; run each; compare stdout:

```python
rc, py_out  = run(["python3", "p.py"])
rc, _       = run(["g++", "-std=c++17", "main.cpp", "-o", "m"]);  cpp_out  = run(["./m"])
rc, java_out = run(["java", "Main.java"])
assert py_out == cpp_out == java_out
```

Ignore the harmless `Picked up JAVA_TOOL_OPTIONS` line from the JVM when comparing.

## Bug report template

```text
Lesson: (name or number)
Language: (Python / C# / C++ / Java) or App + version
What I did:
What I expected:
What happened (paste the last error lines):
```
