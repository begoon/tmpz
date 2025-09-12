def rule_110_step(row: list[int]) -> list[int]:
    row = list(row)
    n = len(row)
    out = [0] * n

    for i in range(n):
        left = row[(i - 1) % n]
        c = row[i]
        right = row[(i + 1) % n]
        s = left + c + right  # count of ones in the 3-cell neighborhood

        # Rule 110 via counts:
        # sums: 0 -> 0, 3 -> 0, 2 -> 1
        # sum==1 needs a tie-break:
        #   010 -> 1
        #   100 -> 0
        #   001 -> 1
        if s == 2:
            out[i] = 1
        elif s == 0 or s == 3:
            out[i] = 0
        else:  # s == 1
            if c == 1:
                out[i] = 1  # 010
            else:
                out[i] = right  # 001 -> 1, 100 -> 0
    return out


def run_rule_110(initial: list[int], steps: int) -> list[list[int]]:
    grid = [list(initial)]
    for _ in range(steps):
        grid.append(rule_110_step(grid[-1]))
    return grid


def render_grid(grid: list[list[int]], on: str = "█", off: str = ".") -> str:
    return "\n".join("".join(on if x else off for x in row) for row in grid)


if __name__ == "__main__":
    width, steps = 32, 10
    initial = [0] * ((width - 1) // 2) + [1] + [0] * (width // 2)
    grid = run_rule_110(initial, steps)
    print(render_grid(grid))
