# Mastermind

A Mastermind code-breaking solver implemented in three languages: Python, V, and Zig.

## Overview

Mastermind is a two-player game. One player chooses a secret code of 4 pegs
from 6 colors (1296 possible codes); the other player guesses, and after each
guess receives feedback:

- `<in-place>` — pegs with the right color in the right position
- `<by-value>` — pegs with the right color in the wrong position

This project plays the guesser. You (or any opponent) pick a secret code in
your head; the program proposes a guess, you type back the feedback, and it
converges on the code — guaranteed in at most 5 moves, ~4.48 on average.

## Approach

All three implementations use **Knuth's five-guess algorithm** (1977):

1. Start with the full universe of 1296 codes as candidates.
2. For every possible guess `g` in the universe, partition the current
   candidate set by the feedback each candidate would return against `g`.
   The size of the largest partition is `g`'s worst-case score.
3. Pick the guess with the smallest worst case (minimax). Break ties by
   preferring a guess that is itself still a candidate, then lexicographically.
4. After playing the chosen guess, receive feedback and eliminate every
   candidate that would not have produced that feedback.
5. Repeat until `in-place == 4`.

Knuth proved this strategy solves any 4-peg / 6-color game in ≤ 5 guesses.

## Implementations

| Dir | Language | Notes |
|-----|----------|-------|
| `python/` | Python 3.9+ | `mastermind.py` is the clean reference; `mastermind_cached.py` memoizes feedback. Strings `"AABB"` as codes, `Counter` for by-value. No dependencies. |
| `v/` | V | Integer-encoded codes (1111..6666). Two independent `compare` implementations cross-validated in `mastermind_test.v` over all 1296×1296 pairs. |
| `zig/` | Zig | Same integer encoding. Two variants: a monolithic CLI (`zig/mastermind.zig`) and a `Game` struct with a WASM FFI layer (`zig/wasm/`). |

All three share the same minimax ranking and tie-breaking rules, so they
produce the same guess sequence given identical feedback.

### Running

```
just python   # cd python && python3 mastermind.py
just v        # cd v && v test . && v run mastermind.v
just zig      # cd zig && zig test mastermind.zig && zig run mastermind.zig
```

## License

MIT — see [LICENSE](LICENSE).
