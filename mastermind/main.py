import sys
from collections import Counter, defaultdict
from itertools import product

PEG_COUNT = 4
COLORS = "ABCDEF"  # 6 colors

ALL_CODES = ["".join(p) for p in product(COLORS, repeat=PEG_COUNT)]


def feedback(probe: str, candidate: str) -> tuple[int, int]:
    """Return (in-place, by-value) for probe vs candidate."""

    in_place = sum(p == c for p, c in zip(probe, candidate))

    probe_rest = Counter([p for p, c in zip(probe, candidate) if p != c])
    candidate_rest = Counter([c for p, c in zip(probe, candidate) if p != c])

    by_value = sum((probe_rest & candidate_rest).values())

    return in_place, by_value


def consistent_with_history(
    candidate: str,
    history: list[tuple[str, tuple[int, int]]],
) -> bool:
    return all(
        feedback(guess, candidate) == feedback for guess, feedback in history
    )


def minimax_pick(candidates: list[str], universe: list[str]) -> str:
    best_score = None
    best_guess = None

    # Precompute feedback buckets with respect to candidate set for each
    # possible guess: S_C,<i,j> = number of candidates that would yield
    # feedback <i,j> to guess C.
    for probe in universe:
        buckets = defaultdict(int)
        for candidate in candidates:
            v = feedback(probe, candidate)
            buckets[v] += 1
        worst = max(buckets.values(), default=0)

        # Track the best (minimax)
        # Tie-breaking: (worst, not_in_candidates, guess_lexicographically)
        rank_tuple = (worst, probe not in candidates, probe)
        if best_score is None or rank_tuple < best_score:
            best_score = rank_tuple
            best_guess = probe

    return best_guess


def rules():
    print("mastermind: knuth's minimax strategy (4 pegs, 6 colors)\n")
    print(f"colors: {', '.join(COLORS)}")
    print(f"pegs: {PEG_COUNT} (e.g., A{COLORS[0]}{COLORS[0]}{COLORS[1]})")
    print()
    print("<in-place> = exact matches (right color, right position)")
    print("<by-value> = color-only matches (right color, wrong position)")
    print()


def parse_feedback(s: str) -> tuple[int, int] | None:
    s = s.strip().lower()
    if s in {"q", "quit", "exit"}:
        print("bye!")
        sys.exit(0)
    parts = s.replace(",", " ").split()
    if len(parts) != 2:
        return None
    try:
        b, w = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if 0 <= b <= PEG_COUNT and 0 <= w <= PEG_COUNT and b + w <= PEG_COUNT:
        return (b, w)
    return None


def main():
    rules()
    universe = ALL_CODES[:]  # all possible guesses
    candidates = ALL_CODES[:]  # still-possible candidates
    history: list[tuple[str, tuple[int, int]]] = []

    # First guess:
    # Let the algorithm choose: with classic parameters this typically
    # yields an "xxxy"-style guess like AAAB depending on tie-breaks.
    guess = minimax_pick(candidates, universe)

    step = 1
    while True:
        print(f"guess {step}: {guess}")
        feedback = None
        while feedback is None:
            v = input("enter feedback '<in-place> <by-value>' (e.g., 2 1): ")
            feedback = parse_feedback(v)
            if feedback is None:
                print("(!) enter two integers like '2 1' (b+w ≤ 4).")
        b, w = feedback

        history.append((guess, feedback))

        if b == PEG_COUNT:
            print(f"solved in {step} guess(es)")
            return

        candidates = [
            c for c in candidates if consistent_with_history(c, history)
        ]

        if not candidates:
            print("(!) no codes remain consistent with the feedback provided")
            return

        guess = minimax_pick(candidates, universe)
        step += 1


if __name__ == "__main__":
    main()
