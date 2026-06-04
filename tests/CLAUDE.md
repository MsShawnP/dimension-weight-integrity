# Test conventions for this project's `tests/`

This file applies when Claude is working in `dimension-weight-integrity/tests/`.

## What gets tested

- Public-facing functions and behaviors.
- Edge cases surfaced during `/clarify`.
- Anything in FAILURES.md that has a corresponding fix in code.

## What doesn't need a test

- Glue code (one-line wrappers, trivial mappings).
- Configuration constants.
- Pure type definitions.

## Structure

- Mirror the source tree: `src/foo/bar.ext` -> `tests/foo/bar.test.ext`.
- One file per source module unless tests are huge.
- Group related tests by behavior, not by function name.

## Test names

- Describe what the test verifies, in plain English.
- Bad: `test_function_1`, `tests parseConfig`.
- Good: `parses_config_when_file_has_trailing_comma`, `returns_empty_array_when_input_is_null`.

## Setup and teardown

- Prefer fresh state per test over shared mutable state.
- If setup is heavy (DB, network), pin it explicitly and document why.

## Assertions

- One concept per test. If a test asserts five unrelated things, split it.
- Assertions should print useful failure messages.

## Mocks and fakes

- Mock at the boundary (network, filesystem, time), not internal pure functions.
- If you mock a function, comment why.

## Running

- Tests must be runnable with a single command. Document it in README.md.
- A failing test is more useful than an unrun test.

## When a test fails

- Read the actual output, not what you expected to see.
- Bisect: which change broke it?
- Don't suppress with `skip` or `xfail` without a PLAN item to come back.
