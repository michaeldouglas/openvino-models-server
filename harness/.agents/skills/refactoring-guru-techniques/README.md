# refactoring-guru-skill

An **Agent Skill** for environments that support agent skills: while assisting with code, it turns the public **refactoring** and **design patterns** material from [Refactoring.Guru](https://refactoring.guru/) into actionable guidance and quick-reference lists, **without tying the skill to any one programming language**.

## What this project does

- Condenses the [Refactoring](https://refactoring.guru/refactoring) track—**code smells**, **refactoring techniques**, and a **refactoring mindset** (small steps, preserve behavior, name smells before large moves)—into `SKILL.md`.
- Presents the **22 classic GoF-style patterns** from [Design Patterns](https://refactoring.guru/design-patterns) in one-line “typical forces” tables to discourage applying patterns without justification.
- Adds **“Guidance for the AI during coding”** at the top of `SKILL.md`: default behavior for the agent when writing, editing, reviewing, or explaining design (small steps, refactorings before patterns, run checks, and so on).

This repository is a **pedagogical index and agent workflow**, not a verbatim copy of the Refactoring.Guru site; full prose, diagrams, and examples remain on the official site.

## Repository layout

| File | Purpose |
|------|---------|
| [SKILL.md](./SKILL.md) | Main skill: YAML front matter + AI coding guidance + smell / technique / pattern lists |
| [reference.md](./reference.md) | Supplement: URL map, how refactoring and patterns fit together, etc. |
| [README.md](./README.md) | This file |

Cursor’s convention for the primary skill file is **`SKILL.md`** (that casing). Keep that filename so the skill is discovered correctly.

## How to use (Cursor)

1. **Personal skill (all projects)**
   Copy or symlink this directory to `~/.cursor/skills/refactoring-guru-techniques/` (the folder name may vary, but it must contain `SKILL.md`).

2. **Project-only**
   Copy it under `.cursor/skills/refactoring-guru-techniques/` in the repository.

3. After the skill is enabled in Cursor, conversations about **refactoring, design review, maintainability, smells, or pattern choice** should follow the rules and catalog in `SKILL.md`.

Exact paths may differ by Cursor version—check your local docs. If the skill does not load, verify the `name` and `description` fields at the top of `SKILL.md`.

## Acknowledgements and usage

- Taxonomy and terminology belong to **Refactoring.Guru** and its authors; this project only **references and structures** that material so humans and AI share the same vocabulary and workflow.
- For in-depth learning, use the official sites:
  - [Refactoring](https://refactoring.guru/refactoring)
  - [Design Patterns](https://refactoring.guru/design-patterns)

## License

If you add a license file to this repository, state it there; none is bundled by default. For republishing or commercial use of Refactoring.Guru text or illustrations, follow their [Content Usage Policy](https://refactoring.guru/content-usage-policy) and related terms.
