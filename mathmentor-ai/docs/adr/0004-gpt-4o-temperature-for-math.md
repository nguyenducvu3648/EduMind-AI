# ADR 0004: Use GPT-4o With Temperature 0.3 for Math Generation

## Context
Math tutoring requires correctness, stable notation, and concise pedagogical sequencing. Highly creative decoding increases the chance of algebra mistakes, inconsistent formatting, and unnecessary elaboration.

## Decision
Use GPT-4o as the primary generation model with temperature `0.3`.

## Alternatives Considered
- Temperature 0.0: maximally deterministic, but can become brittle and less conversational.
- Temperature 0.7+: more varied explanations, but higher risk for math and LaTeX drift.
- Smaller local model: lower marginal cost, but weaker reasoning quality and more maintenance burden for v1.0.

## Consequences
Low temperature favors repeatable, accurate solutions while leaving enough flexibility for tutoring tone and Socratic responses. Math correctness still requires post-processing, retrieval grounding, and evaluation because decoding settings alone do not guarantee correctness.
