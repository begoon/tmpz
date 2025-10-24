package main

import (
	"math"
	"sort"
)

const (
	N        = 15
	empty    = byte('.')
	human    = byte('X')
	computer = byte('O')
)

type direction struct {
	r, c int
}

var directions = []direction{{1, 0}, {0, 1}, {1, 1}, {1, -1}}

type Move struct {
	r, c int
}

func (m Move) isEmpty() bool {
	return m.r == -1 && m.c == -1
}

type Game struct {
	Board [N][N]byte
	Depth int
	Turn  byte // whose turn now
}

func NewGame(depth int) *Game {
	g := &Game{Depth: depth, Turn: human}
	for r := range N {
		for c := range N {
			g.Board[r][c] = empty
		}
	}
	return g
}

func inRC(r, c int) bool { return r >= 0 && r < N && c >= 0 && c < N }
func in(m Move) bool     { return inRC(m.r, m.c) }

func (g *Game) at(m Move) byte      { return g.Board[m.r][m.c] }
func (g *Game) emptyAt(m Move) bool { return g.at(m) == empty }

func (g *Game) place(m Move, p byte) bool {
	if !in(m) || g.at(m) != empty {
		return false
	}
	g.Board[m.r][m.c] = p
	return true
}

func (g *Game) unplace(m Move) { g.Board[m.r][m.c] = empty }

func (g *Game) isFull() bool {
	for r := range N {
		for c := range N {
			if g.emptyAt(Move{r, c}) {
				return false
			}
		}
	}
	return true
}

func (g *Game) checkWinFrom(m Move, player byte) bool {
	for _, dir := range directions {
		count := 1
		// forward
		v := Move{r: m.r + dir.r, c: m.c + dir.c}
		for in(v) && g.at(v) == player {
			count++
			v.r += dir.r
			v.c += dir.c
		}
		// backward
		v = Move{r: m.r - dir.r, c: m.c - dir.c}
		for in(v) && g.at(v) == player {
			count++
			v.r -= dir.r
			v.c -= dir.c
		}
		if count >= 5 {
			return true
		}
	}
	return false
}

// pattern weights
const (
	winScore            = 1_000_000
	openFour            = 100_000
	closedFour          = 10_000
	openThree           = 1_500
	closedThree         = 300
	openTwo             = 80
	closedTwo           = 20
	doubleWinningThreat = 120_000 // creating two+ winning threats next turn
	doubleOpenThrees    = 60_000  // creating two+ open-threes (..AAA..) at once
)

func (g *Game) evaluate() int {
	// positive favors computer, negative favors human.
	score := 0

	// base contiguous-run heuristic
	score += g.evaluateFor(computer)
	score -= g.evaluateFor(human)

	// enhanced pattern heuristic for "broken" shapes (gapped threes/fours)
	score += g.patternEvalFor(computer)
	score -= g.patternEvalFor(human)

	candidates := g.candidates()

	// double-threat potential (very strong)
	score += g.doubleThreatEvalFor(computer, candidates)
	score -= g.doubleThreatEvalFor(human, candidates)

	// double open-threes (..AAA..) creator
	score += g.doubleOpenThreeEvalFor(computer, candidates)
	score -= g.doubleOpenThreeEvalFor(human, candidates)
	return score
}

func (g *Game) evaluateFor(p byte) int {
	score := 0
	for r := range N {
		for c := range N {
			if g.at(Move{r, c}) != p {
				continue
			}
			for _, d := range directions {
				// Start of a sequence? ensure previous in this dir isn't same
				// player to avoid double counting.
				m := Move{r: r - d.r, c: c - d.c}
				if in(m) && g.at(m) == p {
					continue
				}
				count := 0
				m2 := Move{r: r, c: c}
				for in(m2) && g.at(m2) == p {
					count++
					m2.r += d.r
					m2.c += d.c
				}
				openEnds := 0
				// check one end before start
				if in(m) && g.at(m) == empty {
					openEnds++
				}
				// check one end after the last piece
				if in(m2) && g.at(m2) == empty {
					openEnds++
				}
				score += scoreSequence(count, openEnds)
			}
		}
	}
	return score
}

func scoreSequence(count, openEnds int) int {
	switch {
	case count >= 5:
		return winScore
	case count == 4 && openEnds == 2:
		return openFour
	case count == 4 && openEnds == 1:
		return closedFour
	case count == 3 && openEnds == 2:
		return openThree
	case count == 3 && openEnds == 1:
		return closedThree
	case count == 2 && openEnds == 2:
		return openTwo
	case count == 2 && openEnds == 1:
		return closedTwo
	default:
		return 0
	}
}

type weightedPattern struct {
	pattern string
	weight  int
}

// linesFor builds all straight lines (rows, columns, diagonals) for a perspective p.
// It encodes: p -> 'A', empty -> '.', opponent/border -> 'B', and pads each line with a
// leading and trailing 'B' so pattern edges are easy to reason about.
func (g *Game) linesFor(player byte) []string {
	opponent := human
	if player == human {
		opponent = computer
	}
	enc := func(b byte) byte {
		switch b {
		case player:
			return 'A'
		case empty:
			return '.'
		default: // opponent
			return 'B'
		}
	}
	lines := make([]string, 0, N*4)
	// rows
	for r := range N {
		buf := make([]byte, 0, N+2)
		buf = append(buf, 'B')
		for c := range N {
			buf = append(buf, enc(g.at(Move{r, c})))
		}
		buf = append(buf, 'B')
		lines = append(lines, string(buf))
	}
	// columns
	for c := range N {
		buf := make([]byte, 0, N+2)
		buf = append(buf, 'B')
		for r := 0; r < N; r++ {
			buf = append(buf, enc(g.at(Move{r, c})))
		}
		buf = append(buf, 'B')
		lines = append(lines, string(buf))
	}
	// diagonals (r-c constant)
	for start := 0; start < N; start++ {
		// top row -> down-right
		// r, c := 0, start
		m := Move{r: 0, c: start}
		buf := []byte{'B'}
		for in(m) {
			buf = append(buf, enc(g.at(m)))
			m.r++
			m.c++
		}
		buf = append(buf, 'B')
		if len(buf) > 6 {
			lines = append(lines, string(buf))
		}
	}
	for start := 1; start < N; start++ {
		// left col (excluding [0,0]) -> down-right
		m := Move{r: start, c: 0}
		buf := []byte{'B'}
		for in(m) {
			buf = append(buf, enc(g.at(m)))
			m.r++
			m.c++
		}
		buf = append(buf, 'B')
		if len(buf) > 6 {
			lines = append(lines, string(buf))
		}
	}
	// anti-diagonals (r+c constant)
	for start := 0; start < N; start++ {
		// top row -> down-left
		m := Move{r: 0, c: start}
		buf := []byte{'B'}
		for in(m) {
			buf = append(buf, enc(g.at(m)))
			m.r++
			m.c--
		}
		buf = append(buf, 'B')
		if len(buf) > 6 {
			lines = append(lines, string(buf))
		}
	}
	for start := 1; start < N; start++ {
		// right col (excluding [0,N-1]) -> down-left
		// r, c := start, N-1
		m := Move{r: start, c: N - 1}
		buf := []byte{'B'}
		for in(m) {
			buf = append(buf, enc(g.at(m)))
			m.r++
			m.c--
		}
		buf = append(buf, 'B')
		if len(buf) > 6 {
			lines = append(lines, string(buf))
		}
	}
	_ = opponent // opp unused, but kept for clarity of perspective
	return lines
}

func countPatterns(s, pattern string) int {
	if len(pattern) == 0 {
		return 0
	}
	count := 0
	for i := 0; i+len(pattern) <= len(s); i++ {
		if s[i:i+len(pattern)] == pattern {
			count++
		}
	}
	return count
}

func (g *Game) patternEvalFor(p byte) int {
	// Only add weights for gapped/broken shapes to avoid double-counting
	// with contiguous evaluator.
	// A = current player stones, . = empty, B = opponent/border.
	patterns := []weightedPattern{
		// broken (gapped) fours
		{pattern: ".AAA.A.", weight: 70000},
		{pattern: ".AA.AA.", weight: 80000},
		{pattern: "BAAA.A.", weight: 9000},
		{pattern: ".AAA.AB", weight: 9000},
		{pattern: "BAA.AA.", weight: 10000},
		{pattern: ".AA.AAB", weight: 10000},
		// broken threes (open)
		{pattern: ".AA.A.", weight: 1400},
		{pattern: ".A.AA.", weight: 1400},
		// broken threes (closed)
		{pattern: "BAA.A.", weight: 250},
		{pattern: ".A.AAB", weight: 250},
		{pattern: "B.AA.A.", weight: 250},
		{pattern: ".AA.AB", weight: 250},
		// small bonus for split-twos to help shape building
		{pattern: ".A.A.", weight: 60},
	}
	lines := g.linesFor(p)
	score := 0
	for _, line := range lines {
		for _, pattern := range patterns {
			score += countPatterns(line, pattern.pattern) * pattern.weight
		}
	}
	return score
}

// Double-threat detection

// Heuristic: a move is a double-threat if, after playing it, there are at least two
// distinct winning moves available for the same side (i.e., two or more immediate
// finishes next turn). We scan a limited candidate set for efficiency.
func (g *Game) doubleThreatEvalFor(p byte, candidates []Move) int {
	best := 0
	for _, m := range candidates {
		if g.at(m) != empty {
			continue
		}
		g.place(m, p)
		// if this move already wins, the regular evaluator handles it, skip it
		if g.checkWinFrom(m, p) {
			g.unplace(m)
			continue
		}
		wins := g.countLocalImmediateWinsFrom(m, p)
		if wins > best {
			best = wins
		}
		g.unplace(m)
		if best >= 3 {
			break
		}
	}
	if best >= 2 {
		return doubleWinningThreat * (best - 1)
	}
	return 0
}

// count strict/broken open-threes on just the 4 lines through m (for side p)
func (g *Game) openThreeCountsAround(m Move, player byte) (strict, broken int) {
	lines := g.linesThrough(m, player)
	for _, line := range lines {
		strict += countPatterns(line, ".AAA.")
		broken += countPatterns(line, ".AA.A.")
		broken += countPatterns(line, ".A.AA.")
	}
	return
}

// count immediate wins for side p after m is already placed,
// scanning only empties along the 4 lines through m
func (g *Game) countLocalImmediateWinsFrom(m Move, player byte) int {
	seen := make(map[int]struct{})

	// Helper to add a cell if it’s empty.
	rememeber := func(v Move) {
		if in(v) && g.emptyAt(v) {
			seen[v.r*N+v.c] = struct{}{}
		}
	}

	for _, d := range directions {
		// find start of the line
		m := Move{m.r, m.c}
		for in(Move{m.r - d.r, m.c - d.c}) {
			m.r -= d.r
			m.c -= d.c
		}
		// traverse line, collect empty cells
		for in(m) {
			if g.at(m) == empty {
				rememeber(m)
			}
			m.r += d.r
			m.c += d.c
		}
	}

	// test only those empty cells
	wins := 0
	for rc := range seen {
		r, c := rc/N, rc%N
		m := Move{r: r, c: c}
		g.place(m, player)
		if g.checkWinFrom(m, player) {
			wins++
		}
		g.unplace(m)
	}
	return wins
}

// scores moves that create two or more open-threes at once.
func (g *Game) doubleOpenThreeEvalFor(player byte, candidates []Move) int {
	bestTotal, bestStrict := 0, 0
	for _, m := range candidates {
		if !g.emptyAt(m) {
			continue
		}
		g.place(m, player)
		if g.checkWinFrom(m, player) {
			g.unplace(m)
			continue
		}
		strict, broken := g.openThreeCountsAround(m, player)
		total := strict + broken
		if total > bestTotal || (total == bestTotal && strict > bestStrict) {
			bestTotal, bestStrict = total, strict
		}
		g.unplace(m)
		if bestTotal >= 4 { // cap early for rare huge forks
			break
		}
	}
	if bestTotal >= 2 {
		w := doubleOpenThrees * (bestTotal - 1) // baseline
		if bestStrict == 0 {
			// all-broken double-threes are a bit weaker: scale down
			w = (w * 7) / 10 // 70%
		}
		return w
	}
	return 0
}

// encodes for perspective player: player -> 'A', empty -> '.', opponent -> 'B'
func (g *Game) encodeFor(player byte, pattern byte) byte {
	if pattern == player {
		return 'A'
	}
	if pattern == empty {
		return '.'
	}
	return 'B'
}

// return the 4 padded lines (row, col, diag, anti) that pass through m,
// encoded for perspective p, each padded with 'B' at both ends.
func (g *Game) linesThrough(m Move, player byte) []string {
	lines := make([]string, 0, 4)

	build := func(dr, dc int) string {
		// back to start
		v := Move{r: m.r, c: m.c}
		for in(Move{r: v.r - dr, c: v.c - dc}) {
			v.r -= dr
			v.c -= dc
		}
		buf := []byte{'B'}
		for in(v) {
			buf = append(buf, g.encodeFor(player, g.at(v)))
			v.r += dr
			v.c += dc
		}
		buf = append(buf, 'B')
		return string(buf)
	}

	// horizontal, vertical, diag ↘, anti-diag ↙
	lines = append(lines, build(0, 1))
	lines = append(lines, build(1, 0))
	lines = append(lines, build(1, 1))
	lines = append(lines, build(1, -1))
	return lines
}

// generate candidate moves: all empty cells within distance 2 of any stone
func (g *Game) candidates() []Move {
	seen := make(map[int]bool)
	moves := make([]Move, 0)
	occupied := false
	for r := range N {
		for c := range N {
			if g.emptyAt(Move{r, c}) {
				continue
			}
			occupied = true
			for dr := -2; dr <= 2; dr++ {
				for dc := -2; dc <= 2; dc++ {
					m := Move{r: r + dr, c: c + dc}
					if !in(m) || g.at(m) != empty {
						continue
					}
					rc := m.r*N + m.c
					if !seen[rc] {
						seen[rc] = true
						moves = append(moves, m)
					}
				}
			}
		}
	}
	if !occupied {
		// first move: center
		return []Move{{N / 2, N / 2}}
	}
	// order by proximity to center and quick heuristic
	center := Move{N / 2, N / 2}
	sort.Slice(moves, func(i, j int) bool {
		di := abs(moves[i].r-center.r) + abs(moves[i].c-center.c)
		dj := abs(moves[j].r-center.r) + abs(moves[j].c-center.c)
		return di < dj
	})
	return moves
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

// winningMoves returns all moves for player p that immediately make five-in-a-row.
// helper: does (r,c) touch at least one stone of p?
func (g *Game) adjacentTo(r, c int, player byte) bool {
	for dr := -1; dr <= 1; dr++ {
		for dc := -1; dc <= 1; dc++ {
			if dr == 0 && dc == 0 {
				continue
			}
			m := Move{r: r + dr, c: c + dc}
			if in(m) && g.at(m) == player {
				return true
			}
		}
	}
	return false
}

// winningMoves returns all moves for player p that immediately make five-in-a-row.
// Optimized: test only empties adjacent to p's stones, then confirm with checkWinFrom.
func (g *Game) winningMoves(player byte) []Move {
	moves := make([]Move, 0)
	for r := range N {
		for c := range N {
			if !g.emptyAt(Move{r, c}) {
				continue
			}
			// quick adjacency prefilter (sound: any winning square must touch a p-stone)
			if !g.adjacentTo(r, c, player) {
				continue
			}
			m := Move{r, c}
			g.place(m, player)
			won := g.checkWinFrom(m, player) // local check is enough here
			g.unplace(m)
			if won {
				moves = append(moves, m)
			}
		}
	}
	return moves
}

func (g *Game) minimax(depth int, alpha, beta int, maximizing bool, lastMove Move) (int, Move) {
	if !lastMove.isEmpty() {
		// the side who just moved is the opposite of 'maximizing'
		justPlayed := computer
		if maximizing {
			justPlayed = human
		}
		if g.checkWinFrom(lastMove, justPlayed) {
			if justPlayed == computer {
				return winScore, Move{-1, -1}
			}
			return -winScore, Move{-1, -1}
		}
	}

	if depth == 0 || g.isFull() {
		return g.evaluate(), Move{-1, -1}
	}

	moves := g.candidates()

	// tactical forcing: play immediate win if available; otherwise,
	// restrict to blocking opponent's immediate wins.
	player := computer
	opponent := human
	if !maximizing {
		player, opponent = human, computer
	}
	finishers := g.winningMoves(player)
	if len(finishers) > 0 {
		// win this turn
		return winScore - 1, finishers[0]
	}
	blockers := g.winningMoves(opponent)
	if len(blockers) > 0 {
		// only consider blocking moves to avoid instant loss
		moves = blockers
	}

	// ---

	type scored struct {
		move  Move
		score int
	}

	ordered := make([]scored, 0, len(moves))

	for _, m := range moves {
		g.place(m, player)
		score := g.evaluate()
		g.unplace(m)
		ordered = append(ordered, scored{m, score})
	}

	sort.Slice(ordered, func(i, j int) bool {
		if maximizing {
			return ordered[i].score > ordered[j].score
		}
		return ordered[i].score < ordered[j].score
	})

	// ---

	bestMove := Move{-1, -1}

	if maximizing {
		value := math.MinInt / 2
		for _, scoredMove := range ordered {
			g.place(scoredMove.move, computer)
			// if this move allows any immediate human win next round, don't play it
			if len(g.winningMoves(human)) > 0 {
				score := -winScore + 1
				g.unplace(scoredMove.move)
				if score > value {
					value = score
					bestMove = scoredMove.move
				}
				if value > alpha {
					alpha = value
				}
				if alpha >= beta {
					break
				}
				continue
			}
			score, _ := g.minimax(depth-1, alpha, beta, false, scoredMove.move)
			g.unplace(scoredMove.move)
			if score > value {
				value = score
				bestMove = scoredMove.move
			}
			if value > alpha {
				alpha = value
			}
			if alpha >= beta {
				break
			}
		}
		return value, bestMove
	}

	// minimizing
	value := math.MaxInt / 2
	for _, scoreMove := range ordered {
		g.place(scoreMove.move, human)
		// if this move allows any immediate computer win next round, don't play it
		if len(g.winningMoves(computer)) > 0 {
			score := winScore - 1
			g.unplace(scoreMove.move)
			if score < value {
				value = score
				bestMove = scoreMove.move
			}
			if value < beta {
				beta = value
			}
			if alpha >= beta {
				break
			}
			continue
		}
		score, _ := g.minimax(depth-1, alpha, beta, true, scoreMove.move)
		g.unplace(scoreMove.move)
		if score < value {
			value = score
			bestMove = scoreMove.move
		}
		if value < beta {
			beta = value
		}
		if alpha >= beta {
			break
		}
	}
	return value, bestMove
}
