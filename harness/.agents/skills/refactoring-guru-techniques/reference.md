# Refactoring.Guru — reference map

Supplement to [SKILL.md](SKILL.md). Read when the user wants deeper ties to site sections or teaching material.

## Site roots

- Home: https://refactoring.guru/
- Refactoring track: https://refactoring.guru/refactoring
- Design patterns track: https://refactoring.guru/design-patterns

## Refactoring subtopics (site IA)

Typical top-level pages under the refactoring track include: what refactoring is, clean code, technical debt, when and how to refactor, the smell catalog, the refactoring technique catalog, and premium course material. Prefer linking readers to the specific smell or technique page on the site when giving long-form explanations (URLs follow readable slugs).

## Design pattern subtopics

The patterns section covers: what a pattern is, history, benefits, classification (creational / structural / behavioral), criticism (when patterns hurt), the pattern catalog, and multi-language code examples. Use the criticism and classification pages when the user asks whether a pattern is appropriate.

## Using patterns with refactoring

- **Refactoring** names *mechanical* structure changes often driven by *smells*.
- **Patterns** name *recurring designs*; applying them may change API shape or allocation of responsibilities—coordinate with the user if that implies behavior or contract changes.
- **Order of work**: reduce smells with small refactorings first; introduce a pattern only when forces match and the simpler design is insufficient.

## Language examples

The site documents examples in many languages (e.g. C#, C++, Go, Java, PHP, Python, Ruby, Rust, Swift, TypeScript). When illustrating a pattern or refactor, match the project’s language and style rather than copying Java-centric samples verbatim.
