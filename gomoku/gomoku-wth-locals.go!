package main

import (
	"flag"
	"fmt"
	"math"
	"math/rand"
	"sort"
	"time"

	"github.com/jupiterrider/purego-sdl3/sdl"
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

func (m Move) None() bool {
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

func (g *Game) freePlaces(v []Move) {
	v = v[:0]
	for r := range N {
		for c := range N {
			if g.at(Move{r, c}) == empty {
				v = append(v, Move{r, c})
			}
		}
	}
}

func (g *Game) isFull() bool {
	for r := 0; r < N; r++ {
		for c := 0; c < N; c++ {
			if g.Board[r][c] == empty {
				return false
			}
		}
	}
	return true
}

func (g *Game) isFull_(free []Move) bool {
	return len(free) == 0
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

// Pattern weights (tuned roughly)
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
	// Positive favors computer, negative favors human.
	score := 0
	// base contiguous-run heuristic
	score += g.evaluateFor(computer)
	score -= g.evaluateFor(human)

	// enhanced pattern heuristic for "broken" shapes (gapped threes/fours)
	score += g.patternEvalFor(computer)
	score -= g.patternEvalFor(human)

	candidates := g.candidates()
	_ = candidates

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
				// Start of a sequence? ensure previous in this dir isn't same player to avoid double counting.
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

func scoreSequence(cnt, openEnds int) int {
	switch {
	case cnt >= 5:
		return winScore
	case cnt == 4 && openEnds == 2:
		return openFour
	case cnt == 4 && openEnds == 1:
		return closedFour
	case cnt == 3 && openEnds == 2:
		return openThree
	case cnt == 3 && openEnds == 1:
		return closedThree
	case cnt == 2 && openEnds == 2:
		return openTwo
	case cnt == 2 && openEnds == 1:
		return closedTwo
	default:
		return 0
	}
}

type pattern struct {
	pattern string
	weight  int
}

// linesFor builds all straight lines (rows, columns, diagonals) for a perspective p.
// It encodes: p -> 'A', empty -> '.', opponent/border -> 'B', and pads each line with a
// leading and trailing 'B' so pattern edges are easy to reason about.
func (g *Game) linesFor(p byte) []string {
	opponent := human
	if p == human {
		opponent = computer
	}
	enc := func(b byte) byte {
		switch b {
		case p:
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
	// Only add weights for gapped/broken shapes to avoid double-counting with contiguous evaluator.
	// A = current player stones; . = empty; B = opponent/border.
	patterns := []pattern{
		// Broken (gapped) fours
		{pattern: ".AAA.A.", weight: 70000},
		{pattern: ".AA.AA.", weight: 80000},
		{pattern: "BAAA.A.", weight: 9000},
		{pattern: ".AAA.AB", weight: 9000},
		{pattern: "BAA.AA.", weight: 10000},
		{pattern: ".AA.AAB", weight: 10000},
		// Broken threes (open)
		{pattern: ".AA.A.", weight: 1400},
		{pattern: ".A.AA.", weight: 1400},
		// Broken threes (closed)
		{pattern: "BAA.A.", weight: 250},
		{pattern: ".A.AAB", weight: 250},
		{pattern: "B.AA.A.", weight: 250},
		{pattern: ".AA.AB", weight: 250},
		// Small bonus for split-twos to help shape building
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

// ===== Double-threat detection =====
// Heuristic: a move is a double-threat if, after playing it, there are at least two
// distinct winning moves available for the same side (i.e., two or more immediate
// finishes next turn). We scan a limited candidate set for efficiency.
func (g *Game) doubleThreatEvalFor(p byte, candidates []Move) int {
	// candidates := g.candidates()
	best := 0
	for _, m := range candidates {
		// if g.at(m) != empty {
		// 	continue
		// }
		g.place(m, p)
		// If this move already wins, the regular evaluator handles it; skip here
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
func (g *Game) openThreeCountsAround(m Move, p byte) (strict, broken int) {
	lines := g.linesThrough(m, p)
	for _, ln := range lines {
		strict += countPatterns(ln, ".AAA.")
		broken += countPatterns(ln, ".AA.A.")
		broken += countPatterns(ln, ".A.AA.")
	}
	return
}

// Count immediate wins for side p after m is already placed,
// scanning only empties along the 4 lines through m.
// Count immediate wins for side p after m is already placed,
// scanning only empties along the 4 lines through m.
func (g *Game) countLocalImmediateWinsFrom(m Move, p byte) int {
	seen := make(map[int]struct{})

	// Helper to add a cell if it’s empty.
	rememeber := func(v Move) {
		if in(v) && g.at(v) == empty {
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
		g.place(m, p)
		if g.checkWinFrom(m, p) {
			wins++
		}
		g.unplace(m)
	}
	return wins
}

// Scores moves that create two or more open-threes at once.
func (g *Game) doubleOpenThreeEvalFor(player byte, candidates []Move) int {
	// candidates := g.candidates()
	bestTot, bestStrict := 0, 0
	for _, m := range candidates {
		// if g.emptyAt(m) {
		// 	continue
		// }
		g.place(m, player)
		if g.checkWinFrom(m, player) {
			g.unplace(m)
			continue
		}
		s, b := g.openThreeCountsAround(m, player)
		tot := s + b
		if tot > bestTot || (tot == bestTot && s > bestStrict) {
			bestTot, bestStrict = tot, s
		}
		g.unplace(m)
		if bestTot >= 4 { // cap early for rare huge forks
			break
		}
	}
	if bestTot >= 2 {
		w := doubleOpenThrees * (bestTot - 1) // baseline
		if bestStrict == 0 {
			// all-broken double-threes are a bit weaker: scale down
			w = (w * 7) / 10 // 70%
		}
		return w
	}
	return 0
}

// Encodes for perspective p: p -> 'A', empty -> '.', opponent -> 'B'
func (g *Game) encFor(player byte, pattern byte) byte {
	if pattern == player {
		return 'A'
	}
	if pattern == empty {
		return '.'
	}
	return 'B'
}

// Return the 4 padded lines (row, col, diag, anti) that pass through m,
// encoded for perspective p, each padded with 'B' at both ends.
func (g *Game) linesThrough(m Move, p byte) []string {
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
			buf = append(buf, g.encFor(p, g.at(v)))
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
func (g *Game) adjacentTo(r, c int, p byte) bool {
	for dr := -1; dr <= 1; dr++ {
		for dc := -1; dc <= 1; dc++ {
			if dr == 0 && dc == 0 {
				continue
			}
			m := Move{r: r + dr, c: c + dc}
			if in(m) && g.at(m) == p {
				return true
			}
		}
	}
	return false
}

// winningMoves returns all moves for player p that immediately make five-in-a-row.
// Optimized: test only empties adjacent to p's stones, then confirm with checkWinFrom.
func (g *Game) winningMoves(p byte) []Move {
	moves := make([]Move, 0)
	for r := range N {
		for c := range N {
			if !g.emptyAt(Move{r, c}) {
				continue
			}
			// quick adjacency prefilter (sound: any winning square must touch a p-stone)
			if !g.adjacentTo(r, c, p) {
				continue
			}
			m := Move{r, c}
			g.place(m, p)
			won := g.checkWinFrom(m, p) // local check is enough here
			g.unplace(m)
			if won {
				moves = append(moves, m)
			}
		}
	}
	return moves
}

func (g *Game) minimax(depth int, alpha, beta int, maximizing bool, last Move) (int, Move) {
	free := []Move{}
	g.freePlaces(free)

	if last.r != -1 {
		// The side who just moved is the opposite of 'maximizing'
		justPlayed := computer
		if maximizing {
			justPlayed = human
		}
		if g.checkWinFrom(last, justPlayed) {
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

	// Tactical forcing: play immediate win if available; otherwise,
	// restrict to blocking opponent's immediate wins.
	player := computer
	opponent := human
	if !maximizing {
		player, opponent = human, computer
	}
	finishers := g.winningMoves(player)
	if len(finishers) > 0 {
		// Win this turn.
		return winScore - 1, finishers[0]
	}
	blockers := g.winningMoves(opponent)
	if len(blockers) > 0 {
		// Only consider blocking moves to avoid instant loss.
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

// sum of contiguous-run scores on the 4 lines through m for player p.
// If includeCenter is true, we treat m as if it is occupied by p (used AFTER placing).
// func (g *Game) localContiguousScoreAt(m Move, p byte, includeCenter bool) int {
// 	total := 0
// 	for _, d := range directions {
// 		// Count contiguous stones forward from m
// 		f := 0
// 		v := Move{m.r + d.r, m.c + d.c}
// 		for in(v) && g.at(v) == p {
// 			f++
// 			v.r += d.r
// 			v.c += d.c
// 		}

// 		// Count contiguous stones backward from m
// 		b := 0
// 		v = Move{m.r - d.r, m.c - d.c}
// 		for in(v) && g.at(v) == p {
// 			b++
// 			v.r -= d.r
// 			v.c -= d.c
// 		}

// 		// merged count depends on whether m is occupied by p
// 		cnt := f + b
// 		if includeCenter {
// 			cnt++ // count m itself
// 		}

// 		// open ends around the merged run
// 		openEnds := 0
// 		if includeCenter {
// 			// just outside the merged run including m
// 			v = Move{r: m.r + (f+1)*d.r, c: m.c + (f+1)*d.c}
// 			if in(v) && g.at(v) == empty {
// 				openEnds++
// 			}
// 			// r, c = m.R-(b+1)*d[0], m.C-(b+1)*d[1]
// 			v = Move{r: m.r - (b+1)*d.r, c: m.c - (b+1)*d.c}
// 			if in(v) && g.at(v) == empty {
// 				openEnds++
// 			}
// 		} else {
// 			// m is empty; each side's open end is right next to m
// 			v = Move{r: m.r + f*d.r, c: m.c + f*d.c}
// 			if in(v) && g.at(v) == empty {
// 				openEnds++
// 			}
// 			v = Move{r: m.r - b*d.r, c: m.c - b*d.c}
// 			if in(v) && g.at(v) == empty {
// 				openEnds++
// 			}
// 		}

// 		total += scoreSequence(cnt, openEnds)
// 	}
// 	return total
// }

// Local delta around m for `player` (positive good for `player`).
// func (g *Game) localDeltaEval(m Move, player byte) int {
// 	opponent := human
// 	if player == human {
// 		opponent = computer
// 	}

// 	// BEFORE (m empty)
// 	playerBefore := g.localContiguousScoreAt(m, player, false)
// 	opponentBefore := g.localContiguousScoreAt(m, opponent, false)

// 	// AFTER (place player at m)
// 	g.place(m, player)
// 	playerAfter := g.localContiguousScoreAt(m, player, true)

// 	// opponent sees the center as blocked; don't include center for them
// 	opponentAfter := g.localContiguousScoreAt(m, opponent, false)
// 	g.unplace(m)

// 	return (playerAfter - playerBefore) - (opponentAfter - opponentBefore)
// }

func run(g *Game) {
	if !sdl.SetHint(sdl.HintRenderVSync, "1") {
		panic(sdl.GetError())
	}
	defer sdl.Quit()
	if !sdl.Init(sdl.InitVideo) {
		panic(sdl.GetError())
	}

	var window *sdl.Window
	var renderer *sdl.Renderer
	if !sdl.CreateWindowAndRenderer("Gomoku (SDL3)", 1024, 768, sdl.WindowResizable, &window, &renderer) {
		panic(sdl.GetError())
	}
	defer sdl.DestroyRenderer(renderer)
	defer sdl.DestroyWindow(window)

	turnText := func() string {
		if g.Turn == human {
			return "Your turn"
		}
		return "Computer thinking…"
	}
	sdl.SetWindowTitle(window, "Gomoku (SDL3) - "+turnText())

	var gameOver bool
	var gameOverMsg string

	var lastMove Move = Move{-1, -1}

	lastMove = Move{-1, -1}

	for {
		draw := func() {
			// draw
			sdl.SetRenderDrawColor(renderer, 240, 228, 200, 255)
			sdl.RenderClear(renderer)
			var w, h int32
			sdl.GetWindowSize(window, &w, &h)
			drawBoard(renderer, int(w), int(h))
			drawStones(renderer, g, lastMove)
			sdl.RenderPresent(renderer)
			sdl.SetWindowTitle(window, "Gomoku (SDL3) - "+turnText())
			if gameOver {
				sdl.SetWindowTitle(window, gameOverMsg)
			}
		}
		draw()

		var event sdl.Event
		for sdl.PollEvent(&event) {
			switch event.Type() {
			case sdl.EventQuit:
				return
			case sdl.EventKeyDown:
				if event.Key().Scancode == sdl.ScancodeEscape {
					return
				}
			case sdl.EventMouseMotion:
				if g.Turn != human {
					break
				}
				mx, my := int(event.Motion().X), int(event.Motion().Y)
				var w, h int32
				sdl.GetWindowSize(window, &w, &h)
				m, ok := mousePositionToMove(mx, my, int(w), int(h))
				if ok {
					if m == lastMove || g.at(m) != empty {
						break
					}
					lastMove = m
					g.place(m, human)
					eval := g.evaluate()
					// delta := g.localDeltaEval(m, human)
					fmt.Printf("board evaluation: %d\n", eval)
					g.unplace(m)
					draw()
				}
			case sdl.EventMouseButtonDown:
				if gameOver {
					break
				}
				if g.Turn != human {
					break
				}
				mx, my := int(event.Button().X), int(event.Button().Y)
				var w, h int32
				sdl.GetWindowSize(window, &w, &h)
				m, ok := mousePositionToMove(mx, my, int(w), int(h))
				if ok {
					if g.place(m, human) {
						draw()
						printBoard(g)
						if g.checkWinFrom(m, human) {
							gameOver = true
							gameOverMsg = "You win! ✨"
						}
						free := []Move{}
						g.freePlaces(free)
						if !gameOver && g.isFull() {
							gameOver = true
							gameOverMsg = "Draw."
						}
						if !gameOver {
							g.Turn = computer
							// compute AI move immediately
							fmt.Println("computer is thinking...")
							started := time.Now()
							_, best := g.minimax(g.Depth, math.MinInt/2, math.MaxInt/2, true, Move{-1, -1})
							elapsed := time.Since(started)
							fmt.Printf("computer chose move (%d, %d) in %v\n", best.r, best.c, elapsed)
							if best.r == -1 {
								cands := g.candidates()
								best = cands[rand.Intn(len(cands))]
							}
							g.place(best, computer)
							lastMove = best
							// draw()
							printBoard(g)
							// check win
							if g.checkWinFrom(best, computer) {
								gameOver = true
								gameOverMsg = "Computer wins! 🤖"
							}
							free := []Move{}
							g.freePlaces(free)
							if !gameOver && g.isFull() {
								gameOver = true
								gameOverMsg = "Draw."
							}
							g.Turn = human
						}
					}
				}
			}
		}
	}
}

func drawBoard(r *sdl.Renderer, w, h int) {
	// Compute square board area with margins
	size := min(h, w)
	margin := max(size/20, 16)
	board := size - 2*margin
	cell := board / N
	// top-left origin
	x0 := (w - board) / 2
	y0 := (h - board) / 2

	// Grid
	sdl.SetRenderDrawColor(r, 60, 60, 60, 255)
	for i := 0; i <= N; i++ {
		sdl.RenderLine(r, float32(x0), float32(y0+i*cell), float32(x0+board), float32(y0+i*cell))
		sdl.RenderLine(r, float32(x0+i*cell), float32(y0), float32(x0+i*cell), float32(y0+board))
	}
}

func drawStones(r *sdl.Renderer, g *Game, lastMove Move) {
	var w, h int32
	sdl.GetRenderOutputSize(r, &w, &h)
	size := min(int(h), int(w))
	margin := max(size/20, 16)
	board := size - 2*margin
	cell := board / N
	x0 := (int(w) - board) / 2
	y0 := (int(h) - board) / 2

	radius := max(cell/2-4, 6)

	for ri := range N {
		for ci := range N {
			ch := g.Board[ri][ci]
			if ch == empty {
				continue
			}
			cx := x0 + ci*cell + cell/2
			cy := y0 + ri*cell + cell/2
			switch ch {
			case computer:
				// O as circle outline
				sdl.SetRenderDrawColor(r, 30, 120, 240, 255)
				drawCircle(r, cx, cy, radius)
			case human:
				// X as two lines
				sdl.SetRenderDrawColor(r, 220, 60, 60, 255)
				pad := radius
				sdl.RenderLine(r, float32(cx-pad), float32(cy-pad), float32(cx+pad), float32(cy+pad))
				sdl.RenderLine(r, float32(cx+pad), float32(cy-pad), float32(cx-pad), float32(cy+pad))
			}
			// highlight last move
			if ri == lastMove.r && ci == lastMove.c {
				sdl.SetRenderDrawColor(r, 0, 200, 0, 255)
				sdl.RenderLine(r, float32(cx-radius-2), float32(cy), float32(cx+radius+2), float32(cy))
				sdl.RenderLine(r, float32(cx), float32(cy-radius-2), float32(cx), float32(cy+radius+2))
			}
		}
	}
}

func printBoard(g *Game) {
	for r := range N {
		for c := range N {
			var ch string
			switch g.at(Move{r, c}) {
			case computer:
				ch = "O"
			case human:
				ch = "X"
			default:
				ch = "."
			}
			fmt.Print(ch, " ")
		}
		fmt.Println()
	}
	fmt.Println()
}

func drawCircle(r *sdl.Renderer, cx, cy, radius int) {
	const segments = 64
	var prevX, prevY int
	for i := 0; i <= segments; i++ {
		ang := float64(i) * (2 * math.Pi / segments)
		x := cx + int(float64(radius)*math.Cos(ang))
		y := cy + int(float64(radius)*math.Sin(ang))
		if i > 0 {
			sdl.RenderLine(r, float32(prevX), float32(prevY), float32(x), float32(y))
		}
		prevX, prevY = x, y
	}
}

func mousePositionToMove(mx, my, w, h int) (m Move, ok bool) {
	size := min(h, w)
	margin := max(size/20, 16)
	board := size - 2*margin
	cell := board / N
	x0 := (w - board) / 2
	y0 := (h - board) / 2
	if mx < x0 || my < y0 || mx >= x0+board || my >= y0+board {
		return m, false
	}
	m.c = (mx - x0) / cell
	m.r = (my - y0) / cell
	if m.r < 0 || m.r >= N || m.c < 0 || m.c >= N {
		return m, false
	}
	return m, true
}

func main() {
	depth := flag.Int("depth", 2, "search depth for AI (2-4 is reasonable)")
	flag.Parse()
	if *depth < 1 {
		*depth = 1
	}

	g := NewGame(*depth)
	run(g)
}
