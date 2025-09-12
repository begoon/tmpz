def rule_110_step(row: list[int]) -> list[int]:
    row = list(row)
    n = len(row)
    RULE = 110  # binary: 0b01101110, mapping neighborhoods 000..111 -> LSB..MSB

    def next_cell(left, c, right) -> int:
        idx = (left << 2) | (c << 1) | right  # neighborhood as a 3-bit number
        return (RULE >> idx) & 1

    out = [0] * n
    for i in range(n):
        left = row[(i - 1) % n]
        c = row[i]
        right = row[(i + 1) % n]
        out[i] = next_cell(left, c, right)
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
