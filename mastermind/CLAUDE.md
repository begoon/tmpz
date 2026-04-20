# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Three parallel implementations of a Mastermind solver (4 pegs, 6 colors) using
**Knuth's minimax five-guess algorithm**. Python is the reference; V and Zig
are compiled ports with WASM variants.

## Commands

Top-level `Justfile` runs each implementation from the repo root:

```
just python   # cd python && python3 mastermind.py
just v        # cd v && v test . && v run mastermind.v
just zig      # cd zig && zig test mastermind.zig && zig run mastermind.zig
```

Per-implementation:

- **Python**: no dependencies; stdlib only. Run `python3 python/mastermind.py`
  (or the `mastermind_cached.py` variant, which memoizes feedback in a dict).
- **V tests**: `cd v && v test .` — runs `mastermind_test.v`, which includes a
  full 1296×1296 cross-validation between `compare_1` and `compare_2`.
- **Zig tests**: `cd zig && zig test mastermind.zig` — runs the `test "compare"`
  block. Run a single test by name with `zig test mastermind.zig --test-filter compare`.
- **Zig WASM**: `cd zig/wasm && just wasm` builds `mastermind.wasm` with
  `ReleaseSmall` and runs `bun index.js` against it. The build exports
  `init/deinit/remaining/tries/guess`.
- **V WASM**: `cd v/wasm && just run` (currently `v -o exe run .`).

## Architecture

All three implementations share the same shape:

1. **Universe** — all 1296 codes generated upfront.
2. **Candidates** — codes still consistent with feedback so far.
3. **Pick** — for every probe in the universe, bucket candidates by the
   feedback each would return; pick the probe minimizing the largest bucket.
   Tie-break: prefer a probe that is itself a candidate, then lex-smallest.
4. **Eliminate** — after real feedback, drop candidates that would not have
   produced it.

Two representations in use:

- **Python** uses strings (`"AABB"`) and `collections.Counter` for the
  by-value match. `mastermind_cached.py` adds a `(probe, candidate)` dict
  cache — the non-cached version is the clean reference.
- **V and Zig** encode codes as integers `1111..6666` (base-6 digits +1).
  Digit extraction is `(v / 10^k) % 10`. Feedback is computed with a small
  fixed-size frequency table — no allocations in the hot path. Elimination
  is done in place by writing `0` to the eliminated slot (so the
  `candidates` array stays size-1296 and iteration skips zeros).

The ranking is packed into a single integer in V/Zig:
`rank = probe + (1 - probe_in_candidates)*10000 + worst_eval*100000`.
This works because probe < 10000; `worst_eval` is the primary key, the
in-candidates bit is the secondary key, and `probe` itself is the tertiary
lex tiebreak.

### Zig: two layouts

- `zig/mastermind.zig` — monolithic CLI. Heap-allocates universe/candidates
  via `GeneralPurposeAllocator`.
- `zig/wasm/` — the refactored version. `mastermind.zig` defines a `Game`
  struct with stack-allocated `[N]u32` arrays and methods
  `init / guess / eliminate`. `wasm.zig` exposes these through an opaque
  pointer handle cast to/from `usize` for JS interop. `main.zig` is a native
  CLI that uses the same `Game`. Prefer this layout when extending.

### Conventions

- Feedback order is **always `(in_place, by_value)`** in that order. Input
  parsing accepts `"1 2"` or `"1,2"`.
- Code `0` is the sentinel for "eliminated slot" in V/Zig — never a valid
  code, since all real codes are in `1111..6666`.
- The V monolithic file intentionally keeps both `compare_1` (unrolled with
  in-place invalidation) and `compare_2` (frequency-map). The test suite
  pins them as equivalent; don't delete one without moving its call sites.

## Known rough edges

- `zig/mastermind.zig` uses `std.debug.print` (stderr) for the user-facing
  REPL, and its input loop prints the hint before reading and does not retry
  on parse error. The V version has a correct retry loop — port that if
  editing.
- `zig/wasm/main.zig` calls `Game.init(allocator)` / `game.deinit`, but the
  current `Game.init()` in `zig/wasm/mastermind.zig` takes no arguments and
  has no `deinit`. This file is out of sync.
- Neither V nor Zig caches the `compare(probe, candidate)` table; each round
  recomputes ~1.68M comparisons. A precomputed 1296×1296 `u8` table (~1.6 MB)
  is the obvious next optimization. Python's `mastermind_cached.py` does the
  dict equivalent.

## Files not to touch casually

- `v/mastermind_test.v` — the `test_1_vs_2` cross-product is a strong
  correctness anchor. Keep it passing.
- `pyproject.toml` / `uv.lock` — intentionally dependency-free.
