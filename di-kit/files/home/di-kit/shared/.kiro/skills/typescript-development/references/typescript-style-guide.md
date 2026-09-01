# TypeScript Style Guide

This is the comprehensive reference for the `typescript-development` skill. It carries the
rationale ("why") and worked examples behind every rule. `SKILL.md` is the terse checklist you
apply on every change; come here when a rule's application is non-obvious, when two rules appear
to conflict, or when you need the reasoning to justify a decision to a reviewer.

It is strongly opinionated and inspired by and adapted from 
[TigerStyle](https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md),
TigerBeetle's coding style guide.

## Design Philosophy

- Design goals are safety, performance, and developer experience. All three matter, and safety
  contributes strongly to developer experience.
- Style is more than readability. Readability is a means to an end, not the end itself.
- Spend mental energy upfront, proactively rather than reactively — effort spent on design is
  dwarfed by the cost of implementation, testing, operation, and maintenance.
- An hour or a day of design is worth weeks or months in production.

## Technical Debt

- Default to zero technical debt. As much as you can, do it right the first time.
- When you discover showstoppers, solve them. Don't let exponential-complexity algorithms or known
  performance hazards slip through.
- What you ship should be solid. You may lack features, but what you have meets your design goals.
  This is the only way to make steady incremental progress.
- From day one, treat compiler and linter warnings at the strictest setting as errors — enable
  `strict` in `tsconfig.json` and fail the build on lint warnings.

## Types & Assertions

Use the type system to make invalid states unrepresentable.

- **Never use `any`.** Use `unknown` at boundaries and narrow it before use. `any` disables the
  checker exactly where you most need it.
- **Narrow types as much as possible** — discriminated unions, literal types, branded types, and
  `never` — so invalid combinations cannot even be constructed.

  ```ts
  // Do: the invalid combinations are impossible to construct.
  type Result =
    | { status: "ok"; value: number }
    | { status: "error"; message: string };

  // Don't: value and message can both be present, or both absent.
  type Result = { ok: boolean; value?: number; message?: string };
  ```

- **Enforce exhaustiveness** when switching on a discriminated union by assigning the default case
  to a `never` variable. Adding a new variant then forces every switch to handle it, or the
  compiler errors.

  ```ts
  function area(shape: Shape): number {
    switch (shape.kind) {
      case "circle":
        return Math.PI * shape.r ** 2;
      case "square":
        return shape.side ** 2;
      default: {
        const _exhaustive: never = shape;
        throw new Error(`Unhandled shape: ${JSON.stringify(_exhaustive)}`);
      }
    }
  }
  ```

- **Constrain generic type parameters with `extends`** rather than leaving them open, so the
  signature documents what a caller may pass and the body can safely access the constrained shape.
  An unconstrained parameter is effectively `unknown` and pushes narrowing onto every use.

  ```ts
  // Do: T is guaranteed to have an `id`, so `.id` is safe and callers are guided.
  function byId<T extends { id: string }>(
    items: readonly T[],
    id: string,
  ): T | undefined {
    return items.find((item) => item.id === id);
  }

  // Don't: T is unconstrained, so `item.id` does not type-check.
  function byId<T>(items: readonly T[], id: string): T | undefined {
    return items.find((item) => item.id === id);
  }
  ```

- **Use `satisfies`** to validate a value against a type without widening its inferred type, so you
  keep both the compile-time check and the precise literal types.

  ```ts
  // Do: `config` is checked against the constraint but keeps its narrow type,
  // so `config.env` is "prod" | "dev", not string.
  const config = {
    env: "prod",
    retries: 3,
  } satisfies Record<string, string | number>;

  // Don't: the annotation widens `env` to string and `retries` to number.
  const config: Record<string, string | number> = { env: "prod", retries: 3 };
  ```

- **Keep return types as simple as possible**, because complexity at the return type propagates to
  every call site — dimensionality is viral through the call chain. Prefer `void` over `boolean`,
  `boolean` over a returned value, and a value over `T | null`.
- Types and runtime validation are a safety net, not a substitute for human understanding. Build a
  precise mental model first, encode it in types and schemas, and write code and comments that
  explain and justify that model to your reviewer.

## Runtime Validation

- **Trust the type system inside the program, but trust nothing at the edges.** Parse all data
  crossing a runtime boundary — HTTP request/response bodies, environment variables, file contents,
  queue messages, database rows — with a schema validator such as Zod.

  ```ts
  import { z } from "zod";

  const User = z.object({
    id: z.string().uuid(),
    age: z.number().int().min(0),
  });
  type User = z.infer<typeof User>;

  const user = User.parse(await res.json()); // throws on an invalid shape
  ```

- **Pair validations**: validate at the point of ingestion, and again at the point of use, egress,
  or persistence, to catch corruption that creeps in between.
- **Assert relationships between configuration constants at startup**, both as a sanity check and
  to document the implicit contract between them.

  ```ts
  if (config.batchSize >= config.maxQueueLength) {
    throw new Error(
      `batchSize (${config.batchSize}) must be < maxQueueLength (${config.maxQueueLength})`,
    );
  }
  ```

- The golden rule: enforce the positive space you *do* expect **and** the negative space you *do
  not* expect. Bugs cluster where data moves across the valid/invalid boundary.

## Error Handling

- **Handle every error.** Never write an empty `catch` or leave a rejected promise unhandled.
- **Chain errors** with the `cause` option (and `AggregateError` when several errors are combined)
  so context is preserved across layers when debugging.

  ```ts
  try {
    await save(user);
  } catch (err) {
    throw new Error("Failed to save user", { cause: err });
  }
  ```

- **Keep custom error subclasses minimal**; only add metadata fields in a domain where they are
  well understood and relevant.
- For failures that are **expected rather than exceptional**, return a success/failure union
  instead of throwing, so failure is a visible part of the signature rather than hidden control
  flow.

  ```ts
  type Parsed = { ok: true; value: number } | { ok: false; error: string };
  ```

## Control Flow

- **Use simple, explicit control flow** for clarity. Do not use recursion for unbounded work:
  TypeScript has no tail-call optimisation in practice, so a deep stack throws `RangeError` — an
  ungraceful crash. Iterate instead.
- **Use as few abstractions as possible**, and add one only when it makes the best sense of the
  domain. Every abstraction can leak, and none are free.
- **Put a fixed upper bound on every loop and queue** to prevent infinite loops and unbounded
  latency (the fail-fast principle). Where a loop is intended never to terminate (e.g. an event
  loop), assert that intent explicitly.
- **Split compound boolean conditions** into simple conditions using nested `if/else` branches, and
  convert long `else if` chains into `else { if {} }` trees, so every branch and case is visible.
- When you write an `if`, **consider whether it needs a matching `else`** so that both the positive
  and negative case are handled or asserted.
- **State invariants positively** rather than as negations. Prefer `if (index < length)` over
  `if (index >= length)` — the former is easier to get right and to read.
- **Do not act directly in reaction to external events.** Let the program run at its own pace and
  batch work rather than context-switching on every event; this keeps control flow under your
  control.
- **Pass options explicitly at the call site** rather than relying on a function's defaults, so
  behaviour does not change silently if those defaults change.
- **Add braces to every `if`** except when the whole statement fits on one line — for consistency
  and defence against "goto fail"-style bugs.

## Variables & Scope

- Declare variables at the smallest possible scope, and minimise the number of variables in scope,
  to reduce the probability that the wrong variable is used.
- Calculate or check variables close to where they are used. Don't introduce a variable before it
  is needed, and don't leave it around after.
- Don't duplicate variables or create additional references to them — this reduces the probability
  that state gets out of sync.

## Functions

- **Keep each function under ~70 lines** — short enough to read without scrolling. There is a sharp
  discontinuity between a function that fits on a screen and one you must scroll through.
- **Aim for the inverse-hourglass shape**: few parameters, a simple return type, and the substance
  in the body.
- **Push `if`s up, push `for`s down**: keep branching (`if`/`switch`) in the parent function and
  move non-branching logic into pure helper functions. Let the parent hold state in locals and have
  helpers compute changes rather than applying them directly, so leaf functions stay pure.
- **Treat every `await` as a suspension point**: state you checked before the `await` may be stale
  afterwards, so re-validate preconditions if other code could have mutated shared state in the
  meantime. Don't assume an assertion at the top of an `async` function still holds lower down.
- **Pair resource acquisition with its cleanup** in the same place — `try/finally`, or
  `await using` with `Symbol.asyncDispose` — separated by newlines from surrounding code, so it is
  obvious at a glance that everything opened is also closed.

  ```ts
  await using conn = await pool.acquire(); // released automatically at scope end
  ```

- When two or more parameters share a type and could be swapped, **take a named options object**
  instead of positional arguments. If an argument can be `null`, name it so the meaning of `null`
  at the call site is clear.

  ```ts
  // Do
  function move(opts: { fromX: number; toX: number }) {}
  // Don't
  function move(fromX: number, toX: number) {}
  ```

- **Put callbacks last** in the parameter list, mirroring that they are invoked last.

## Naming

- **Get the nouns and verbs just right.** Great names capture what a thing is or does and provide a
  crisp, intuitive mental model; they show you understand the domain.
- **Infuse names with meaning.** Specific names that convey behaviour or lifecycle beat generic
  ones (`retryBudget`/`connectionPool` over a bare `manager`; `activeConnection` over `conn2`).
- **Don't overload a name** with different meanings in different contexts.
- **Prefer nouns** for identifiers reused in docs or conversation: `session.expiry` reads better
  than `session.expiring`, and composes into `expiryMsMax`.
- **Do not abbreviate names**, except for ephemeral variables with a very short lifespan such as a
  callback parameter (`items.map((u) => u.id)`).
- **Append units and qualifiers to names, most significant first**, so related variables align:
  `latencyMsMax`, not `maxLatencyMs`.
- **Match the length of related names** so they line up in source: `source`/`target` over
  `src`/`dest`, so `sourceOffset` and `targetOffset` align in calculations.
- **Prefix a helper with the name of its caller** to show the call history: `readSector` and
  `readSectorCallback`.
- **Use long-form flags in scripts** (`--force`, not `-f`); single-letter flags are for interactive
  use only.

## Module & File Layout

- Order matters for readability even though it doesn't affect semantics. A module is read top-down,
  so put the most important things near the top.
- Within a module: define types and interfaces near the top or beside the code that uses them, then
  the main export, then internal helpers below.
- Order class members consistently: static fields, then instance fields, then the constructor, then
  methods, grouping related methods together.
- Extract a complex inline or nested type into a named top-level `type` or `interface` rather than
  inlining it.
- When no order is inherent, sort alphabetically (import groups, object keys, union members), using
  "big-endian" naming so shared prefixes cluster together.

## Off-By-One Errors

- The usual suspects are casual interactions between an `index`, a `count`, and a `size`. Treat
  them as distinct concepts with clear conversions: `count = index + 1` (indexes are 0-based,
  counts 1-based), and `size = count * unit`. This is why units and qualifiers in names matter.
- Make rounding intent explicit with `Math.floor` / `Math.ceil`; never rely on implicit truncation.

## Comments & Documentation

- **Always say why.** The code already shows what it does; use comments to justify why it is written
  that way. Explaining the rationale increases understanding, makes people more likely to adhere,
  and shares the criteria by which to evaluate the decision.
- **Don't forget to say how.** Precede a test with a short comment stating its goal and method, so a
  reader can get up to speed or skip it.
- **Comments are sentences**: a space after `//`, a capital letter, and a full stop (or a colon if
  they introduce what follows). They are well-written prose, not scribblings in the margin. A
  trailing inline comment may be a phrase without punctuation.
- **Write descriptive commit messages.** A PR description is not stored in the repository and is
  invisible in `git blame` — it is not a substitute for a commit message.

## Testing

- **Test exhaustively**: with valid data, with invalid data, and across the transition as valid data
  becomes invalid.
- **Test error and failure paths explicitly.** Simple tests of failure paths prevent the majority of
  catastrophic failures.
- **Never monkey-patch** modules, globals, or object prototypes to make code testable — it couples
  tests to internals and hides integration problems. Instead, inject dependencies so a test can
  supply its own implementation without rewriting the code under test at runtime.
- **Make each test understandable on its own** for whoever it fails for: a clear name, self-contained
  arrange/act/assert, and specific assertion messages, so a failure is intelligible without
  reverse-engineering shared fixtures or other tests.
- **Target 100% coverage.** Mark any uncovered line with an ignore pragma carrying a justification
  from an agreed, finite list, so a coverage gap is always a deliberate, reviewable decision.

  ```ts
  /* v8 ignore next 3 -- defensive: unreachable, guarded by the assertion above */
  ```

  Allowed justifications:
  - an unreachable defensive branch paired with a throw;
  - platform- or environment-specific code that cannot run under test;
  - third-party or generated code the team has chosen not to test directly.

## Performance

- **Design for it first.** The biggest wins come from the design phase — the shape of your data,
  your access patterns, your boundaries — precisely when you can't yet measure. Get the shape right
  first, then measure.
- **Optimise I/O before CPU.** I/O (database round-trips, HTTP calls, disk) is almost always the
  slowest resource, and a single mis-shaped query dwarfs any in-process cleverness.
- **Amortise I/O by batching.** Never issue requests one at a time in a loop. Use bulk queries and
  run independent async work with `Promise.all`.
- **Never block the event loop**; it is a single lane shared by every concurrent request. Chunk or
  offload CPU-heavy work to worker threads.
- **Bound concurrency**, just as you bound everything else. An unbounded `Promise.all` over a large
  array will exhaust connections, memory, or rate limits.

  ```ts
  import pLimit from "p-limit";
  const limit = pLimit(10);
  await Promise.all(items.map((it) => limit(() => process(it))));
  ```

- **Measure what matters to your domain.** Track the latency of whole user-facing operations
  (checkout, search, page load), not isolated micro-benchmarks; a function that is fast alone can
  still make the journey slow.

## Tooling & Dependencies

- Enable `strict` in `tsconfig.json`, and treat compiler and lint warnings as errors that fail the
  build.
- Run the formatter (Prettier / `eslint --fix`) on every change.
- Indent with 2 spaces — visually distinct without eating into the line-length budget in deeply
  nested blocks.
- Cap line length at 100 columns — just enough to fit two copies side-by-side — enforced via
  `printWidth` / `max-len` rather than by eye.
- **Minimise external dependencies.** Each is a supply-chain, safety, and performance risk, and the
  cost compounds in foundational code.
- **Standardise on TypeScript for tooling** (scripts, automation) rather than shell scripts, so they
  are cross-platform, portable, and type-safe. Standardising on one language reduces dimensionality
  as the team grows: slower for you short term, more velocity long term.
- Tools have costs. A small standardised toolbox is simpler to operate than an array of specialised
  instruments each with its own manual — the right tool for the job is often the one you already
  use.
