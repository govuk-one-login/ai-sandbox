---
name: typescript-development
description: Enforce a strict, safety-first TypeScript style when writing or editing code in a Node.js TypeScript project. Apply these directives to every change to TypeScript code.
---

# TypeScript Development

Apply this style to **every** change you make to TypeScript in a Node.js project — new code and
edits alike. The design goals are safety, performance, and developer experience, in that priority
order; safety underpins the other two. Each item below is a concrete rule about the code you
produce, not a loose guideline. Prefer refusing a shortcut over violating a rule; if you must
deviate, say so and say why.

The checklist below is the operational summary. For the rationale behind each rule, worked code
examples, and guidance when rules trade off against each other, read
[`references/typescript-style-guide.md`](references/typescript-style-guide.md). Consult it whenever
a rule's application is non-obvious or you need to justify a decision to a reviewer.

## Types & assertions

- Never use `any`; use `unknown` at boundaries and narrow before use.
- Make invalid states unrepresentable — discriminated unions, literal and branded types.
- Enforce `switch` exhaustiveness by assigning the default case to a `never` variable.
- Constrain generics with `extends`, not open type parameters.
- Use `satisfies` to check a value against a type without widening its inferred type.
- Keep return types simple: prefer `void` > `boolean` > a value > `T | null`.

## Runtime validation

- Parse everything crossing a runtime boundary (HTTP, env vars, files, queue messages, DB rows)
  with a schema validator such as Zod. Trust types inside the program; trust nothing at the edges.
- Pair validations: validate at ingestion and again at use, egress, or persistence.
- Assert relationships between configuration constants at startup.

## Error handling

- Handle every error: no empty `catch`, no unhandled rejection.
- Chain errors with `cause` (and `AggregateError` when combining) to preserve context.
- Keep custom error subclasses minimal.
- For expected failures, return a success/failure union instead of throwing.

## Control flow

- Simple, explicit control flow; no recursion for unbounded work (no TCO) — iterate.
- Use as few abstractions as possible; add one only when it best fits the domain.
- Bound every loop and queue; assert intent for a loop meant never to terminate.
- Split compound conditions into nested `if/else`; turn `else if` chains into `else { if {} }`.
- Consider whether each `if` needs a matching `else`.
- State invariants positively (`if (index < length)`).
- Don't act directly on external events — batch and run at your own pace.
- Pass options explicitly at the call site; don't rely on defaults.
- Brace every `if` unless it fits on one line.

## Variables & scope

- Declare at the smallest possible scope; minimise variables in scope.
- Compute or check variables close to use; don't introduce them early or leave them around.
- Don't duplicate variables or create extra references to them.

## Functions

- Keep each function under ~70 lines.
- Inverse-hourglass shape: few parameters, a simple return type, the substance in the body.
- Push `if`s up, push `for`s down — branching in the parent, pure leaf helpers.
- Re-validate preconditions after every `await`; it is a suspension point where state may go stale.
- Pair resource acquisition with cleanup (`try/finally` or `await using`).
- Use a named options object when parameters share a type or could be swapped.
- Put callbacks last.

## Naming

- Names capture what a thing is or does; specific over generic.
- Don't overload a name across contexts.
- Prefer nouns for identifiers reused in docs or conversation.
- Don't abbreviate, except very short-lived variables such as callback parameters.
- Append units and qualifiers last, most significant first (`latencyMsMax`).
- Match the length of related names so they align (`source`/`target`).
- Prefix a helper with its caller's name (`readSector` / `readSectorCallback`).
- Use long-form flags in scripts (`--force`, not `-f`).

## Module & file layout

- Put the most important things near the top; modules are read top-down.
- Order: types/interfaces near the top or beside their use → main export → internal helpers.
- Order class members: static fields → instance fields → constructor → methods (grouped).
- Extract complex inline or nested types into named top-level `type`/`interface`.
- Sort alphabetically when no order is inherent (imports, keys, union members); use big-endian names.

## Off-by-one

- Treat `index`, `count`, and `size` as distinct: `count = index + 1`, `size = count * unit`.
- Make rounding explicit with `Math.floor` / `Math.ceil`.

## Comments

- Explain why, not what.
- Precede a test with a comment stating its goal and method.
- Comments are full sentences; a trailing inline comment may be an unpunctuated phrase.
- Write descriptive commit messages — a PR description is not a substitute.

## Testing

- Test with valid data, invalid data, and across the valid→invalid transition.
- Test error and failure paths explicitly.
- Never monkey-patch; inject dependencies instead.
- Make each test understandable in isolation: clear name, self-contained arrange/act/assert,
  specific assertions.
- Target 100% coverage; mark gaps with a justified ignore pragma from the agreed list.

## Performance

- Get data shape, access patterns, and boundaries right at design time, then measure.
- Optimise I/O before CPU.
- Batch I/O; never issue requests one at a time in a loop; use `Promise.all` for independent work.
- Never block the event loop; offload CPU-heavy work to worker threads.
- Bound concurrency; never run an unbounded `Promise.all` over a large array.
- Measure whole user-facing operations, not micro-benchmarks.

## Tooling & dependencies

- Enable `strict`; treat compiler and lint warnings as build-failing errors.
- Run the formatter on every change.
- 2-space indentation; 100-column line limit, enforced via config.
- Minimise external dependencies.
- Write scripts and automation in TypeScript.
