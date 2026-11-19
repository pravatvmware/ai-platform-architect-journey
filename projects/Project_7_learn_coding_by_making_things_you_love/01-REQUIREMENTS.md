# 01 · Requirements

## The problem

A father (a DevOps/cloud engineer with experience in AWS, Azure, Docker, Kubernetes and Python, but little web development) wanted to give his son a lasting gift: a way to learn programming that he would actually enjoy.

## The learner

| | |
|---|---|
| **Study** | 3D Animation and Filmmaking (academic stream) |
| **Programming experience** | None |
| **Daily time** | About 20–30 minutes |
| **Tools he will use** | Blender, Maya, Houdini, Unity, Unreal |
| **Hardware** | High-end Windows gaming laptop (Lenovo), iPad, phone, Wacom tablet |
| **Motivation** | Creative; not a "programmer" by interest, so it must not feel like homework |
| **Career direction** | 3D animation, film, design and leadership, not pure software engineering |

## The builder

- Comfortable reading and following steps; **not** a web developer
- About 5 hours a week to build
- Low or free-tier budget; has an Azure account (free tier may run out)
- Wants something he can understand, change and extend later

## Original request

> "Make a tool to learn fun with Python and C# based on interest."

The first idea was C++ because of games, then C# was considered because it matches Unity and fits his goals better. The final decision was to teach **all four** (Python, C#, C++, Java) in the same app so he can choose and compare.

## Functional requirements

1. The learner picks an **interest** (Games, 3D Animation, VFX, Film) and a **language** (Python, C#, C++, Java).
2. Each lesson has **editable, runnable code**, an explanation, syntax notes in simple sentences, a tip, a real-world story and an assignment or remix.
3. A **W3Schools-style curriculum**: Beginner → Intermediate → Expert, learned gradually, with 100 Beginner lessons.
4. **XP, levels and a forgiving streak** to keep motivation without punishing missed days.
5. A **small cartoon mascot** on the right side that reacts to what he does.
6. **Real-world stories** that stay fresh (dynamic from the web, with an offline fallback).
7. Links to the **real tools** he uses (Blender, Maya, Houdini, Unity, Unreal) and small projects he can show friends.
8. A personal **welcome** from his father.

## Non-functional requirements

| Requirement | How it was met |
|---|---|
| **Fun, not homework** | Interest-themed assignments, mascot, XP, mini projects |
| **Short sessions** | Small lessons (roughly 5–15 minutes) |
| **Works on his laptop** | Docker image with all four language runtimes |
| **Works on iPad** | Optional `--lan` mode over home Wi-Fi |
| **Cheap or free** | Runs locally; no cloud bill |
| **Maintainable by a non-web-developer** | One HTML file, plain Python data files, no build step |
| **Safe** | Local only, non-root container, resource limits |
| **Offline-capable** | Everything except the live stories works without internet |

## Original improvement list

| # | Request | Result |
|---|---|---|
| 1 | Host on Azure serverless with the GoDaddy domain | **Deferred**: local Docker chosen for now; plan documented in [Roadmap](09-ROADMAP.md) |
| 2 | Add C++ and Java | ✅ Done |
| 3 | Syntax explained in simple sentences | ✅ Done (generated notes for every lesson) |
| 4 | 100 code sets for Beginner, plus Intermediate and Expert | ✅ 165 path lessons (100 / 40 / 25) |
| 5 | Small cartoon mascot on the right | ✅ Pip, an original character |
| 6 | Real-world stories dynamically from the web | ✅ RSS-based with offline fallback |

Later additions: Tool Track (28 lessons), four Mini Projects, welcome message, Windows start/stop scripts.
