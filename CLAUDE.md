# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ARSNoP (A Roughly Sufficient Number of Parsers) is a pure Python parsing library implementing multiple parsing algorithms for context-free grammars: Earley, LR(0), SLR(1), LR(1), and LALR(1). No external dependencies.

## Running

```bash
# Run the example (TIM format parser)
uv run -m arsnop.example.main
```

Dependencies are listed in `pyproject.toml` (Python ≥3.12, Flask + Flask-CORS for the web demo).

## Testing

- A pytest test suite is included in the `test/` directory.
- Run the tests from the repository root with:

```bash
uv run -m pytest test/ -q
```

- If `pytest` is not installed, install it with `pip install pytest`.
- Shared test fixtures (grammars, parse helpers) live in `test/parser/shift_reduce/generators/conftest.py`.
- Cross-generator consistency tests in `test_consistency.py` verify all LR variants produce the same results.

## Architecture

The pipeline follows: **Input Text → Lexer → Tokens → ParsingEngine → AST → Transformer → Result**

### Key Modules

- **`lexer/`** — Tokenizes input using regex-based terminal definitions. Supports standard, exact-match, and ignored terminals.
- **`grammar/`** — Represents CFGs parsed from BNF-style rules. Computes FIRST/FOLLOW sets (cached via `@functools.cache`), nullability, closure, and successor operations for LR item sets.
- **`parser/`** — Main interface. `parser.from_file(path, parser="earley")` is the factory that reads a grammar file and returns a configured `Parser` instance.
  - **`parser/earley/`** — Top-down dynamic programming parser. Handles all CFGs including ambiguous grammars.
  - **`parser/shift_reduce/`** — Bottom-up LR family. `automaton.py` is the `ParsingEngine` that executes shift-reduce parsing. The `generators/` sub-package builds action/goto tables:
    - `generator.py` — Abstract `Generator` base class (template method pattern: `generate()` orchestrates `_build_states` → action/goto table construction).
    - `lr0.py`, `lr1.py`, `lalr.py`, `lalr_brute_force.py` — Concrete generators for each LR variant.
    - `closure.py` — Parameterized closure computation using `@fixed_point`.
    - `util.py` — The `@fixed_point` decorator: repeatedly applies a pure transformation until convergence (`new_state == state`). Used for closure and lookahead propagation.
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

## Linting

- Ruff is used for linting. Run `uv run ruff check arsnop/ test/` after making changes.

## Typing

- Pyright is configured in strict mode. All new and modified code must pass `uv run pyright arsnop/` with 0 errors.
- Prefer concrete types over `Any`. Use `Any` only when the type is genuinely unconstrained (e.g., user-defined transformer return values).
- Use type aliases (PEP 695 `type` syntax) to reduce verbosity when a complex type appears more than once. Existing aliases live in `arsnop/parser/shift_reduce/types.py`.
- Run `uv run pyright arsnop/` after making changes to catch regressions.

## Code Style

- Keep functions short and singular in purpose. When a function performs multiple
  distinct phases, extract each phase into a named helper with a docstring. The
  top-level function should read like a high-level description of the algorithm.

## Workflow

- Use a feature branch strategy. Always create a new branch off `main` for changes rather than committing directly to `main`.
- Do not include `Co-Authored-By` lines in commit messages.

## Web Demo

An interactive web app for visualizing parser tables and step-by-step parse execution.

```bash
# Start both servers (Flask API + Vite dev server)
make dev

# Or start them individually:
make api   # Flask REST API on http://localhost:5001
make web   # Vite dev server on http://localhost:5173 (proxies /api to Flask)

# Install frontend dependencies (first time only)
make install-web
```

### REST API (`rest/`)

A Flask backend that exposes the parsing library over HTTP:

- **`app.py`** — Flask factory with CORS and blueprint registration.
- **`grammar_store.py`** — Discovers/loads bundled `.bnf` files from `arsnop/resources/`.
- **`serializers.py`** — JSON serialization for domain objects (Production, Item, State, Action/Goto tables, Token, AST).
- **`tracer.py`** — Trace-generating parse loop that mirrors `Automaton.parse()` but records each step.
- **`routes/grammar.py`** — Grammar endpoints: list bundled, load bundled, analyze (FIRST/FOLLOW sets).
- **`routes/parser.py`** — Parse endpoints: generate tables, execute parse with trace.

### Frontend (`web/`)

A React + TypeScript + Vite app using MUI and CodeMirror:

- Grammar editor with bundled grammar selector and parser variant picker (LR0, SLR, LR1, LALR, LALR BF).
- Results panel with tabs: Grammar Info, States, Action/Goto Tables, Parse Trace (stepper + table), AST tree view.
- State managed via Zustand (`web/src/store/useAppStore.ts`).

### Parser Selection

The `from_file()` factory accepts: `"earley"`, `"lr0"`, `"slr"`, `"lr1"`, `"lalr"`, `"lalr_brute_force"`. Earley handles any CFG; the LR variants require deterministic grammars but run in linear time.
