---
name: prose-polish
description: >
  Academic copy-editing pass that makes machine-assisted or stiff prose read more naturally and
  in the author's own voice. Use when asked to "humanize" text, "polish my writing", "remove the
  AI voice", "remove em-dashes", "vary the sentence structure", "make it read more naturally",
  "clean up the thesis prose", or "edit for style". Works on LaTeX (.tex), Markdown, and plain text.
  This is a writing-QUALITY tool, not a detector-evasion tool — see the Scope and ethics note.
---

# Prose Polish

A conservative copy-editing pass for academic writing. It improves readability and voice; it does
**not** rewrite meaning, invent claims, or touch citations, numbers, equations, labels, or results.

## Scope and ethics

This skill exists to make genuine writing read better. It is **not** a tool for evading AI- or
plagiarism-detection systems, and it must not be described or used as one. No text transformation
reliably "beats" a detector, and disguising authorship to deceive an academic-integrity process is
the user's responsibility, not something to optimise for. When someone asks for detection evasion,
redirect to this legitimate quality pass and let them own the authorship/policy decision. Improve the
writing; never promise a detector outcome.

## What it changes (safe, high-value)

1. **Em-dash overuse** — the most common "machine voice" tell. Replace `---` (LaTeX) and `—` (U+2014)
   with the punctuation the sentence actually needs:
   - **Paired** em-dashes (parenthetical aside): convert to a pair of commas, or parentheses if the
     aside is long or already contains commas.
   - **Single** em-dash: comma for a trailing phrase; **colon** if what follows is a list or an
     elaboration; **semicolon** if it joins two independent clauses.
   - **Leave en-dashes (`--`) alone** — they are correct in numeric/page ranges (e.g. `30--60`).
2. **Uniform cadence** — break up runs of same-length, same-shape sentences; vary sentence openings
   so they don't all start with the subject or with a transition word.
3. **Tricolon tic** — thin out repeated "X, Y, and Z" triples when several land in one paragraph.
4. **Hedging and filler** — trim "it is important to note that", "it is worth noting", "plays a
   crucial/pivotal role", "in the modern ... landscape", redundant "Furthermore/Moreover" chains.
5. **Register** — prefer concrete verbs over nominalisations where it doesn't change meaning.

## What it must NOT touch

- Citation commands (`\cite`, `\textcite`, `\parencite`), labels, `\ref`, `\input`, figures, tables.
- Numbers, equations, math mode, units, results, or any factual claim.
- Meaning. If a fix would change what a sentence asserts, leave it and flag it instead.
- TikZ/diagram files (`tikz_*.tex`) — `--`/`---` there can be path syntax.

## How to apply (LaTeX thesis workflow)

1. Inventory tells: count `---` and `—` per prose file (exclude `tikz_*.tex`).
2. Transform em-dashes with the rules above. A blanket `--- → comma` script is a *starting point*
   only — review every single change, because single em-dashes often need a colon/semicolon, not a
   comma, to avoid comma splices.
3. Do a light cadence/cliché pass on paragraphs that read most uniformly.
4. Re-read the diff end to end; confirm no `---`/`—` remain in prose and no meaning shifted.
5. Rebuild: `texts/build_thesis.sh` (writes the next `thesis_vN.pdf`). Confirm the page count and a
   clean log (no undefined refs/citations) before declaring done.
