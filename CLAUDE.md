# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ARSNoP (A Roughly Sufficient Number of Parsers) is a pure Python parsing library implementing multiple parsing algorithms for context-free grammars: Earley, LR(0), SLR(1), LR(1), and LALR(1). No external dependencies.

## Running

```bash
# Run the example (TIM format parser)
uv run -m src.example.main
```

There is no build system or package manager config.

## Testing

- A pytest test suite is included in the `test/` directory.
- Run the tests from the repository root with:

```bash
uv run -m pytest test/ -q
```

- If `pytest` is not installed, install it with `pip install pytest`.

## Architecture

The pipeline follows: **Input Text → Lexer → Tokens → ParsingEngine → AST → Transformer → Result**

### Key Modules

- **`lexer/`** — Tokenizes input using regex-based terminal definitions. Supports standard, exact-match, and ignored terminals.
- **`grammar/`** — Represents CFGs parsed from BNF-style rules. Computes FIRST/FOLLOW sets (cached via `@functools.cache`), nullability, closure, and successor operations for LR item sets.
- **`parser/`** — Main interface. `parser.from_file(path, parser="earley")` is the factory that reads a grammar file and returns a configured `Parser` instance.
  - **`parser/earley/`** — Top-down dynamic programming parser. Handles all CFGs including ambiguous grammars.
  - **`parser/shift_reduce/`** — Bottom-up LR family. `generators.py` builds action/goto tables for LR0/SLR/LR1/LALR. `automaton.py` is the `ParsingEngine` that executes shift-reduce parsing using those tables.
- **`transformer/`** — Visitor-pattern base class for DFS traversal and transformation of ASTs.
- **`utils.py`** — Shared helpers (`flatten`, `print_states`).

### Grammar File Format

Grammar definition files (`.bnf`) use this structure:

```
:GRAMMAR
rule ::= alt1 | alt2
:TERMINALS
TOKEN_NAME regex_pattern
.EXACT
KEYWORD exact_string
.IGNORE
WHITESPACE
```

## Typing

- Pyright is configured in strict mode. All new and modified code must pass `uv run pyright src/` with 0 errors.
- Prefer concrete types over `Any`. Use `Any` only when the type is genuinely unconstrained (e.g., user-defined transformer return values).
- Use type aliases (PEP 695 `type` syntax) to reduce verbosity when a complex type appears more than once. Existing aliases live in `src/parser/shift_reduce/types.py`.
- Run `uv run pyright src/` after making changes to catch regressions.

## Code Style

- Keep functions short and singular in purpose. When a function performs multiple
  distinct phases, extract each phase into a named helper with a docstring. The
  top-level function should read like a high-level description of the algorithm.

## Workflow

- Use a feature branch strategy. Always create a new branch off `main` for changes rather than committing directly to `main`.
- Do not include `Co-Authored-By` lines in commit messages.

### Parser Selection

The `from_file()` factory accepts: `"earley"`, `"lr0"`, `"slr"`, `"lr1"`, `"lalr"`, `"lalr_brute_force"`. Earley handles any CFG; the LR variants require deterministic grammars but run in linear time.
