package main

import (
	"flag"
	"math"
	"math/rand"
	"sort"

	// SDL3 binding
	"github.com/jupiterrider/purego-sdl3/sdl"
)

const (
	N        = 15
	empty    = byte('.')
	human    = byte('X')
	computer = byte('O')
)

var directions = [][2]int{{1, 0}, {0, 1}, {1, 1}, {1, -1}}

type Move struct {
	R, C int
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

func in(r, c int) bool { return r >= 0 && r < N && c >= 0 && c < N }

func (g *Game) place(m Move, p byte) bool {
	if !in(m.R, m.C) || g.Board[m.R][m.C] != empty {
		return false
	}
	g.Board[m.R][m.C] = p
	return true
}

func (g *Game) unplace(m Move) { g.Board[m.R][m.C] = empty }

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

func (g *Game) checkWin(p byte) bool {
	for r := range N {
		for c := range N {
			if g.Board[r][c] != p {
				continue
			}
			for _, d := range directions {
				count := 1
				r2, c2 := r+d[0], c+d[1]
				for in(r2, c2) && g.Board[r2][c2] == p {
					count++
					r2 += d[0]
					c2 += d[1]
				}
				if count >= 5 {
					return true
				}
			}
		}
	}
	return false
}

// Optimized local check: after placing m for player p, only lines through m can win.
func (g *Game) checkWinFrom(m Move, p byte) bool {
	for _, d := range directions {
		cnt := 1
		// forward
		r, c := m.R+d[0], m.C+d[1]
		for in(r, c) && g.Board[r][c] == p {
			cnt++
			r += d[0]
			c += d[1]
		}
		// backward
		r, c = m.R-d[0], m.C-d[1]
		for in(r, c) && g.Board[r][c] == p {
			cnt++
			r -= d[0]
			c -= d[1]
		}
		if cnt >= 5 {
			return true
		}
	}
	return false
}

// Pattern weights (tuned roughly)
const (
	winScore      = 1_000_000
	openFour      = 100_000
	closedFour    = 10_000
	openThree     = 1_500
	closedThree   = 300
	openTwo       = 80
	closedTwo     = 20
	doubleThreatW = 120_000 // creating two+ winning threats next turn
	doubleOTW     = 60_000  // creating two+ open-threes (..AAA..) at once
)

func (g *Game) evaluate() int {
	// Positive favors computer, negative favors human
	score := 0
	// base contiguous-run heuristic
	score += g.evaluateFor(computer)
	score -= g.evaluateFor(human)
	// enhanced pattern heuristic for "broken" shapes (gapped threes/fours)
	score += g.patternEvalFor(computer)
	score -= g.patternEvalFor(human)
	// double-threat potential (very strong)
	score += g.doubleThreatEvalFor(computer)
	score -= g.doubleThreatEvalFor(human)
	// double open-threes (..AAA..) creator
	score += g.doubleOpenThreeEvalFor(computer)
	score -= g.doubleOpenThreeEvalFor(human)
	return score
}

func (g *Game) evaluateFor(p byte) int {
	total := 0
	for r := 0; r < N; r++ {
		for c := 0; c < N; c++ {
			if g.Board[r][c] != p {
				continue
			}
			for _, d := range directions {
				// Start of a sequence? ensure previous in this dir isn't same player to avoid double counting
				pr, pc := r-d[0], c-d[1]
				if in(pr, pc) && g.Board[pr][pc] == p {
					continue
				}
				cnt := 0
				r2, c2 := r, c
				for in(r2, c2) && g.Board[r2][c2] == p {
					cnt++
					r2 += d[0]
					c2 += d[1]
				}
				openEnds := 0
				// check one end before start
				if in(pr, pc) && g.Board[pr][pc] == empty {
					openEnds++
				}
				// check one end after the last piece
				if in(r2, c2) && g.Board[r2][c2] == empty {
					openEnds++
				}
				total += scoreSequence(cnt, openEnds)
			}
		}
	}
	return total
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

// ===== Enhanced pattern scoring: broken (gapped) shapes =====

type pattern struct {
	pat    string
	weight int
}

// linesFor builds all straight lines (rows, columns, diagonals) for a perspective p.
// It encodes: p -> 'A', empty -> '.', opponent/border -> 'B', and pads each line with a
// leading and trailing 'B' so pattern edges are easy to reason about.
func (g *Game) linesFor(p byte) []string {
	opp := human
	if p == human {
		opp = computer
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
	for r := 0; r < N; r++ {
		buf := make([]byte, 0, N+2)
		buf = append(buf, 'B')
		for c := 0; c < N; c++ {
			buf = append(buf, enc(g.Board[r][c]))
		}
		buf = append(buf, 'B')
		lines = append(lines, string(buf))
	}
	// columns
	for c := 0; c < N; c++ {
		buf := make([]byte, 0, N+2)
		buf = append(buf, 'B')
		for r := 0; r < N; r++ {
			buf = append(buf, enc(g.Board[r][c]))
		}
		buf = append(buf, 'B')
		lines = append(lines, string(buf))
	}
	// diagonals (r-c constant)
	for start := 0; start < N; start++ {
		// top row -> down-right
		r, c := 0, start
		buf := []byte{'B'}
		for in(r, c) {
			buf = append(buf, enc(g.Board[r][c]))
			r++
			c++
		}
		buf = append(buf, 'B')
		if len(buf) > 6 {
			lines = append(lines, string(buf))
		}
	}
	for start := 1; start < N; start++ {
		// left col (excluding [0,0]) -> down-right
		r, c := start, 0
		buf := []byte{'B'}
		for in(r, c) {
			buf = append(buf, enc(g.Board[r][c]))
			r++
			c++
		}
		buf = append(buf, 'B')
		if len(buf) > 6 {
			lines = append(lines, string(buf))
		}
	}
	// anti-diagonals (r+c constant)
	for start := 0; start < N; start++ {
		// top row -> down-left
		r, c := 0, start
		buf := []byte{'B'}
		for in(r, c) {
			buf = append(buf, enc(g.Board[r][c]))
			r++
			c--
		}
		buf = append(buf, 'B')
		if len(buf) > 6 {
			lines = append(lines, string(buf))
		}
	}
	for start := 1; start < N; start++ {
		// right col (excluding [0,N-1]) -> down-left
		r, c := start, N-1
		buf := []byte{'B'}
		for in(r, c) {
			buf = append(buf, enc(g.Board[r][c]))
			r++
			c--
		}
		buf = append(buf, 'B')
		if len(buf) > 6 {
			lines = append(lines, string(buf))
		}
	}
	_ = opp // opp unused, but kept for clarity of perspective
	return lines
}

func countAll(s, sub string) int {
	if len(sub) == 0 {
		return 0
	}
	count := 0
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
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
		{pat: ".AAA.A.", weight: 70000},
		{pat: ".AA.AA.", weight: 80000},
		{pat: "BAAA.A.", weight: 9000},
		{pat: ".AAA.AB", weight: 9000},
		{pat: "BAA.AA.", weight: 10000},
		{pat: ".AA.AAB", weight: 10000},
		// Broken threes (open)
		{pat: ".AA.A.", weight: 1400},
		{pat: ".A.AA.", weight: 1400},
		// Broken threes (closed)
		{pat: "BAA.A.", weight: 250},
		{pat: ".A.AAB", weight: 250},
		{pat: "B.AA.A.", weight: 250},
		{pat: ".AA.AB", weight: 250},
		// Small bonus for split-twos to help shape building
		{pat: ".A.A.", weight: 60},
	}
	lines := g.linesFor(p)
	score := 0
	for _, ln := range lines {
		for _, pat := range patterns {
			score += countAll(ln, pat.pat) * pat.weight
		}
	}
	return score
}

// ===== Double-threat detection =====
// Heuristic: a move is a double-threat if, after playing it, there are at least two
// distinct winning moves available for the same side (i.e., two or more immediate
// finishes next turn). We scan a limited candidate set for efficiency.
func (g *Game) doubleThreatEvalFor(p byte) int {
	cands := g.candidates()
	best := 0
	for _, m := range cands {
		if g.Board[m.R][m.C] != empty {
			continue
		}
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
		return doubleThreatW * (best - 1)
	}
	return 0
}

// ===== Double open-threes detection =====
// Counts how many open-threes (".AAA.") exist for side p in the current board view.
// openThreeCountsFor returns counts of strict and broken open-threes for side p.
// strict: ".AAA."; broken: ".AA.A.", ".A.AA."
func (g *Game) openThreeCountsFor(p byte) (strict, broken int) {
	for _, ln := range g.linesFor(p) {
		strict += countAll(ln, ".AAA.")
		broken += countAll(ln, ".AA.A.")
		broken += countAll(ln, ".A.AA.")
	}
	return strict, broken
}

// Count immediate wins for side p after m is already placed,
// scanning only empties along the 4 lines through m.
// Count immediate wins for side p after m is already placed,
// scanning only empties along the 4 lines through m.
func (g *Game) countLocalImmediateWinsFrom(m Move, p byte) int {
	seen := make(map[int]struct{})

	// Helper to add a cell if it’s empty.
	addCell := func(r, c int) {
		if in(r, c) && g.Board[r][c] == empty {
			seen[r*N+c] = struct{}{}
		}
	}

	// Walk each of the 4 directions crossing m.
	dirs := [][2]int{{0, 1}, {1, 0}, {1, 1}, {1, -1}}
	for _, d := range dirs {
		// find start of the line
		r, c := m.R, m.C
		for in(r-d[0], c-d[1]) {
			r -= d[0]
			c -= d[1]
		}
		// traverse line, collect empty cells
		for in(r, c) {
			if g.Board[r][c] == empty {
				addCell(r, c)
			}
			r += d[0]
			c += d[1]
		}
	}

	// Test only those empty cells.
	wins := 0
	for key := range seen {
		r, c := key/N, key%N
		mv := Move{R: r, C: c}
		g.place(mv, p)
		if g.checkWinFrom(mv, p) {
			wins++
		}
		g.unplace(mv)
	}
	return wins
}

// Scores moves that create two or more open-threes at once.
func (g *Game) doubleOpenThreeEvalFor(p byte) int {
	cands := g.candidates()
	bestTot, bestStrict := 0, 0
	for _, m := range cands {
		if g.Board[m.R][m.C] != empty {
			continue
		}
		g.place(m, p)
		if g.checkWinFrom(m, p) {
			g.unplace(m)
			continue
		}
		s, b := g.openThreeCountsAround(m, p)
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
		w := doubleOTW * (bestTot - 1) // baseline
		if bestStrict == 0 {
			// all-broken double-threes are a bit weaker: scale down
			w = (w * 7) / 10 // 70%
		}
		return w
	}
	return 0
}

// Encodes for perspective p: p -> 'A', empty -> '.', opponent -> 'B'
func (g *Game) encFor(p byte, b byte) byte {
	if b == p {
		return 'A'
	}
	if b == empty {
		return '.'
	}
	return 'B'
}

// Return the 4 padded lines (row, col, diag, anti) that pass through m,
// encoded for perspective p, each padded with 'B' at both ends.
func (g *Game) linesThrough(m Move, p byte) []string {
	out := make([]string, 0, 4)

	build := func(dr, dc int) string {
		// back to start
		r, c := m.R, m.C
		for in(r-dr, c-dc) {
			r -= dr
			c -= dc
		}
		buf := []byte{'B'}
		for in(r, c) {
			buf = append(buf, g.encFor(p, g.Board[r][c]))
			r += dr
			c += dc
		}
		buf = append(buf, 'B')
		return string(buf)
	}

	// horizontal, vertical, diag ↘, anti-diag ↙
	out = append(out, build(0, 1))
	out = append(out, build(1, 0))
	out = append(out, build(1, 1))
	out = append(out, build(1, -1))
	return out
}

// Count strict/broken open-threes on just the 4 lines through m (for side p)
func (g *Game) openThreeCountsAround(m Move, p byte) (strict, broken int) {
	lines := g.linesThrough(m, p)
	for _, ln := range lines {
		strict += countAll(ln, ".AAA.")
		broken += countAll(ln, ".AA.A.")
		broken += countAll(ln, ".A.AA.")
	}
	return
}

// Generate candidate moves: all empty cells within distance 2 of any stone
func (g *Game) candidates() []Move {
	seen := make(map[int]bool)
	moves := make([]Move, 0)
	occupied := false
	for r := range N {
		for c := range N {
			if g.Board[r][c] == empty {
				continue
			}
			occupied = true
			for dr := -2; dr <= 2; dr++ {
				for dc := -2; dc <= 2; dc++ {
					r2, c2 := r+dr, c+dc
					if !in(r2, c2) || g.Board[r2][c2] != empty {
						continue
					}
					key := r2*N + c2
					if !seen[key] {
						seen[key] = true
						moves = append(moves, Move{r2, c2})
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
		di := abs(moves[i].R-center.R) + abs(moves[i].C-center.C)
		dj := abs(moves[j].R-center.R) + abs(moves[j].C-center.C)
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
			rr, cc := r+dr, c+dc
			if in(rr, cc) && g.Board[rr][cc] == p {
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
	for r := 0; r < N; r++ {
		for c := 0; c < N; c++ {
			if g.Board[r][c] != empty {
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
	if last.R != -1 {
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
	// Tactical forcing: play immediate win if available; otherwise, restrict to blocking opponent's immediate wins.
	cur := computer
	opp := human
	if !maximizing {
		cur, opp = human, computer
	}
	finishers := g.winningMoves(cur)
	if len(finishers) > 0 {
		// Win this turn.
		return winScore - 1, finishers[0]
	}
	blockers := g.winningMoves(opp)
	if len(blockers) > 0 {
		// Only consider blocking moves to avoid instant loss.
		moves = blockers
	}
	// simple move ordering with shallow eval after placing
	type scored struct {
		m Move
		s int
	}
	ordered := make([]scored, 0, len(moves))
	for _, m := range moves {
		s := g.localDeltaEval(m, cur)
		ordered = append(ordered, scored{m, s})
	}

	sort.Slice(ordered, func(i, j int) bool {
		if maximizing {
			return ordered[i].s > ordered[j].s
		}
		return ordered[i].s < ordered[j].s
	})

	bestMove := Move{-1, -1}
	if maximizing {
		value := math.MinInt / 2
		for _, sc := range ordered {
			g.place(sc.m, computer)
			score, _ := g.minimax(depth-1, alpha, beta, false, sc.m)
			g.unplace(sc.m)
			if score > value {
				value = score
				bestMove = sc.m
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
	for _, sc := range ordered {
		g.place(sc.m, human)
		scVal, _ := g.minimax(depth-1, alpha, beta, true, sc.m)
		g.unplace(sc.m)
		if scVal < value {
			value = scVal
			bestMove = sc.m
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

// sum of contiguous-run scores on the 4 lines through m for player p
func (g *Game) localContigScoreAt(m Move, p byte) int {
	total := 0
	for _, d := range directions {
		// walk backward to the start of this line’s contiguous segment grouping
		// but we actually want to evaluate *segments* on the entire line,
		// so we’ll just count the contiguous sequences that touch the line
		// through m in both directions.

		// Count contiguous stones forward from m
		f := 0
		r, c := m.R+d[0], m.C+d[1]
		for in(r, c) && g.Board[r][c] == p {
			f++
			r += d[0]
			c += d[1]
		}

		// Count contiguous stones backward from m
		b := 0
		r, c = m.R-d[0], m.C-d[1]
		for in(r, c) && g.Board[r][c] == p {
			b++
			r -= d[0]
			c -= d[1]
		}

		cnt := 1 + f + b

		// open ends around the merged run
		openEnds := 0
		// cell after forward
		r, c = m.R+(f+1)*d[0], m.C+(f+1)*d[1]
		if in(r, c) && g.Board[r][c] == empty {
			openEnds++
		}
		// cell before backward
		r, c = m.R-(b+1)*d[0], m.C-(b+1)*d[1]
		if in(r, c) && g.Board[r][c] == empty {
			openEnds++
		}

		total += scoreSequence(cnt, openEnds)
	}
	return total
}

// Estimate the *delta* in contiguous-run score caused by playing m for `cur`
// (positive is good for `cur`). We compute local contiguous scores before and after
// for both sides on the four lines through m and return (cur_after - cur_before)
//   - (opp_after - opp_before).
func (g *Game) localDeltaEval(m Move, cur byte) int {
	opp := human
	if cur == human {
		opp = computer
	}

	// --- measure BEFORE (on current board) ---
	curBefore := g.localContigScoreAt(m, cur)
	oppBefore := g.localContigScoreAt(m, opp)

	// --- measure AFTER placing cur at m ---
	g.place(m, cur)
	curAfter := g.localContigScoreAt(m, cur)
	oppAfter := g.localContigScoreAt(m, opp)
	g.unplace(m)

	return (curAfter - curBefore) - (oppAfter - oppBefore)
}

func runSDL(g *Game) {
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

	for {
		var event sdl.Event
		for sdl.PollEvent(&event) {
			switch event.Type() {
			case sdl.EventQuit:
				return
			case sdl.EventKeyDown:
				if event.Key().Scancode == sdl.ScancodeEscape {
					return
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
				r, c, ok := screenToCell(mx, my, int(w), int(h))
				if ok {
					m := Move{R: r, C: c}
					if g.place(m, human) {
						if g.checkWinFrom(m, human) {
							gameOver = true
							gameOverMsg = "You win! ✨"
						}
						if !gameOver && g.isFull() {
							gameOver = true
							gameOverMsg = "Draw."
						}
						if !gameOver {
							g.Turn = computer
							// compute AI move immediately
							_, best := g.minimax(g.Depth, math.MinInt/2, math.MaxInt/2, true, Move{-1, -1})
							if best.R == -1 {
								cands := g.candidates()
								best = cands[rand.Intn(len(cands))]
							}
							g.place(best, computer)
							if g.checkWinFrom(best, computer) {
								gameOver = true
								gameOverMsg = "Computer wins! 🤖"
							}
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

		// draw
		sdl.SetRenderDrawColor(renderer, 240, 228, 200, 255) // board background
		sdl.RenderClear(renderer)
		var w, h int32
		sdl.GetWindowSize(window, &w, &h)
		drawBoard(renderer, int(w), int(h))
		drawStones(renderer, g)
		sdl.RenderPresent(renderer)
		sdl.SetWindowTitle(window, "Gomoku (SDL3) - "+turnText())
		if gameOver {
			sdl.SetWindowTitle(window, gameOverMsg)
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

func drawStones(r *sdl.Renderer, g *Game) {
	var w, h int32
	sdl.GetRenderOutputSize(r, &w, &h)
	size := min(int(h), int(w))
	margin := max(size/20, 16)
	board := size - 2*margin
	cell := board / N
	x0 := (int(w) - board) / 2
	y0 := (int(h) - board) / 2

	radius := max(cell/2-4, 6)

	for rIdx := range N {
		for cIdx := range N {
			ch := g.Board[rIdx][cIdx]
			if ch == empty {
				continue
			}
			cx := x0 + cIdx*cell + cell/2
			cy := y0 + rIdx*cell + cell/2
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
		}
	}
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

func screenToCell(mx, my, w, h int) (r, c int, ok bool) {
	size := min(h, w)
	margin := size / 20
	if margin < 16 {
		margin = 16
	}
	board := size - 2*margin
	cell := board / N
	x0 := (w - board) / 2
	y0 := (h - board) / 2
	if mx < x0 || my < y0 || mx >= x0+board || my >= y0+board {
		return 0, 0, false
	}
	c = (mx - x0) / cell
	r = (my - y0) / cell
	if r < 0 || r >= N || c < 0 || c >= N {
		return 0, 0, false
	}
	return r, c, true
}

// ===================== Main =====================

func main() {
	depth := flag.Int("depth", 2, "search depth for AI (2-4 is reasonable)")
	flag.Parse()
	if *depth < 1 {
		*depth = 1
	}

	g := NewGame(*depth)
	runSDL(g)
}
