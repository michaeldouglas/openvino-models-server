---
name: refactoring-guru-techniques
description: >-
  Operational guidance for AI-assisted coding using Refactoring.Guru’s catalogs:
  code smells, refactoring moves, and classic design patterns. Use when writing,
  editing, or reviewing code; when the user asks for cleaner structure,
  refactoring, design patterns, smells, maintainability, or “how should this be
  designed” in any language or stack.
---

# Refactoring.Guru techniques (language-agnostic)

Concepts and names below follow the public catalogs at [Refactoring.Guru — Refactoring](https://refactoring.guru/refactoring) and [Refactoring.Guru — Design Patterns](https://refactoring.guru/design-patterns). Express ideas in the user’s language and idioms; do not assume a specific syntax unless the codebase dictates it.

## Guidance for the AI during coding

Use this section as **binding workflow** whenever you generate patches, propose designs, or review code—not only when the user says “refactor.”

1. **Default to small, safe edits**: Prefer localized changes that match existing style; avoid drive-by rewrites unrelated to the request.
2. **Preserve behavior unless told otherwise**: Treat structural improvement as behavior-preserving; call out any intentional behavior change explicitly.
3. **Name smells before big moves**: If you widen scope, briefly identify which smells (from the catalog below) you are addressing and why.
4. **Prefer refactorings over patterns**: Apply catalog **refactoring techniques** first; introduce a **design pattern** only when forces clearly match and a simpler type/module/function split is insufficient.
5. **Do not pattern-spray**: Skip Singleton and other heavy patterns when plain functions, modules, or composition already solve the problem.
6. **Keep APIs honest**: Separate queries from modifiers where it reduces surprise; avoid hidden global mutation and deep message chains when alternatives exist.
7. **Use checks**: After edits, run or suggest the project’s tests, linters, or type checks when available; if none exist, state what you verified manually.
8. **Explain trade-offs briefly**: When choosing a pattern or a larger structure, one short paragraph on forces, risks, and alternatives is enough.

## How to use this skill (summary)

1. **Clarify intent**: Refactoring improves structure without changing observable behavior (unless the user explicitly wants a behavior change).
2. **Find smells first**: Name likely smells, then pick the smallest refactor that addresses the root cause—not the largest pattern.
3. **Work in small steps**: One mechanical change at a time; keep tests or checks green when they exist.
4. **Prefer simplicity**: A pattern is a tool, not a badge. Skip it when a simpler model fits.

## Refactoring mindset (from the Refactoring track)

- **Dirty vs clean**: Favor readable, understandable, maintainable structure over cleverness.
- **Technical debt**: Treat smells as signals; prioritize fixes that reduce change risk and duplication.
- **When to refactor**: When it makes the next change cheaper, when a smell blocks understanding, or when duplication diverges—not as speculative rewrites without motivation.
- **How to refactor**: Decompose problems, automate or repeat checks after each step, and preserve behavior unless agreed otherwise.

## Code smells (catalog names)

Use these as a checklist when diagnosing structure. Group names match the site’s taxonomy.

### Bloaters

Long Method, Large Class, Primitive Obsession, Long Parameter List, Data Clumps.

### Object-orientation abusers

Switch Statements, Temporary Field, Refused Bequest, Alternative Classes with Different Interfaces.

### Change preventers

Divergent Change, Shotgun Surgery, Parallel Inheritance Hierarchies.

### Dispensables

Comments (as deodorant), Duplicate Code, Lazy Class, Data Class, Dead Code, Speculative Generality.

### Couplers

Feature Envy, Inappropriate Intimacy, Message Chains, Middle Man.

### Other

Incomplete Library Class.

## Refactoring techniques (catalog names)

Pick techniques that directly target the smell; combine small steps rather than one large rewrite.

### Composing methods

Extract Method, Inline Method, Extract Variable, Inline Temp, Replace Temp with Query, Split Temporary Variable, Remove Assignments to Parameters, Replace Method with Method Object, Substitute Algorithm.

### Moving features between objects

Move Method, Move Field, Extract Class, Inline Class, Hide Delegate, Remove Middle Man, Introduce Foreign Method, Introduce Local Extension.

### Organizing data

Self Encapsulate Field, Replace Data Value with Object, Change Value to Reference, Change Reference to Value, Replace Array with Object, Duplicate Observed Data, Change Unidirectional Association to Bidirectional, Change Bidirectional Association to Unidirectional, Replace Magic Number with Symbolic Constant, Encapsulate Field, Encapsulate Collection, Replace Type Code with Class, Replace Type Code with Subclasses, Replace Type Code with State/Strategy, Replace Subclass with Fields.

### Simplifying conditional expressions

Decompose Conditional, Consolidate Conditional Expression, Consolidate Duplicate Conditional Fragments, Remove Control Flag, Replace Nested Conditional with Guard Clauses, Replace Conditional with Polymorphism, Introduce Null Object, Introduce Assertion.

### Simplifying method calls

Rename Method, Add Parameter, Remove Parameter, Separate Query from Modifier, Parameterize Method, Replace Parameter with Explicit Methods, Preserve Whole Object, Replace Parameter with Method Call, Introduce Parameter Object, Remove Setting Method, Hide Method, Replace Constructor with Factory Method, Replace Error Code with Exception, Replace Exception with Test.

### Dealing with generalization

Pull Up Field, Pull Up Method, Pull Up Constructor Body, Push Down Method, Push Down Field, Extract Subclass, Extract Superclass, Extract Interface, Collapse Hierarchy, Form Template Method, Replace Inheritance with Delegation, Replace Delegation with Inheritance.

## Design patterns (GoF catalog on the site)

Patterns are **recurring solutions** to recurring design problems. Prefer the simplest design that meets constraints; introduce a pattern when forces (variation, extension, lifecycle, performance, etc.) clearly match.

### Creational

| Pattern | Typical force (one line) |
|--------|---------------------------|
| Factory Method | Subclasses choose which product type to create. |
| Abstract Factory | Families of related products must stay consistent. |
| Builder | Stepwise construction of complex or variant-rich objects. |
| Prototype | Clone as cheaper or more flexible than subclass explosion. |
| Singleton | Truly single shared instance (easy to overuse—justify global state). |

### Structural

| Pattern | Typical force (one line) |
|--------|---------------------------|
| Adapter | Bridge incompatible interfaces without changing core logic. |
| Bridge | Separate abstraction from implementation so both vary independently. |
| Composite | Uniform tree/part-whole operations over hierarchies. |
| Decorator | Add responsibilities dynamically without subclass sprawl. |
| Facade | Simplify a large or awkward subsystem behind one entry point. |
| Flyweight | Share intrinsic state to support huge numbers of similar objects. |
| Proxy | Control access, lazy init, logging, remote indirection, etc. |

### Behavioral

| Pattern | Typical force (one line) |
|--------|---------------------------|
| Chain of Responsibility | Pass a request along a chain until something handles it. |
| Command | Encapsulate requests as objects for undo, queueing, logging. |
| Iterator | Traverse aggregates without exposing internal structure. |
| Mediator | Reduce many-to-many coupling via a central coordination object. |
| Memento | Capture and restore object state without breaking encapsulation. |
| Observer | Notify dependents automatically when subject state changes. |
| State | Object behavior changes cleanly with internal phase/mode changes. |
| Strategy | Swap algorithms/policies without changing callers. |
| Template Method | Fixed skeleton with customizable steps in subclasses/hooks. |
| Visitor | Add operations across a stable class hierarchy without editing each type. |

## Agent output pattern (when explaining design or refactors)

When the user asks for refactor or design guidance—or when you propose a non-trivial structural change—use this shape so output stays actionable:

1. **Smells**: Bullet the top smells with file/symbol anchors if known.
2. **Forces**: One sentence on what is changing in the design problem.
3. **Moves**: Ordered list of refactoring technique names (and patterns only if clearly justified).
4. **Risks**: Coupling, concurrency, API compatibility, or data migration notes.

## Further reading

- [What is refactoring](https://refactoring.guru/refactoring) and nested topics (clean code, technical debt, process).
- [Design patterns hub](https://refactoring.guru/design-patterns) including classification, benefits, and criticism—use to avoid over-engineering.

For extended notes and URL map, see [reference.md](reference.md).
