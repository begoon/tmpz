package main

import (
	"errors"
	"log/slog"
	"syscall/js"
	"time"

	"gomoku/gomoku"
)

var NoResponse = js.ValueOf(nil)

func minimax(this js.Value, args []js.Value) any {
	if len(args) < 2 {
		slog.Error("minimax: missing arguments: expected 2 (board, depth)")
		return NoResponse
	}

	game, err := convertBoard(args[0])
	if err != nil {
		slog.Error("minimax: convert board", "error", err)
		return NoResponse
	}

	gomoku.PrintBoard(game)

	depth := args[1].Int()
	slog.Info("minimax", "depth", depth)
	if depth <= 0 {
		depth = 2
	}

	start := time.Now()
	value, move := game.Minimax(depth)
	elapsed := time.Since(start).Seconds()
	slog.Info("minimax", "value", value, "move", move, "duration", elapsed)

	return map[string]any{
		"move":     map[string]any{"r": move.R, "c": move.C},
		"duration": elapsed,
	}
}

func evaluation(this js.Value, args []js.Value) any {
	if len(args) < 1 {
		slog.Error("evaluation: missing arguments: expected 1 (board)")
		return NoResponse
	}

	game, err := convertBoard(args[0])
	if err != nil {
		slog.Error("evaluation: convert board", "error", err)
		return NoResponse
	}

	value := game.Evaluate()
	slog.Info("evaluation", "value", value)

	return map[string]any{"value": value}
}

func endgame(this js.Value, args []js.Value) any {
	if len(args) < 1 {
		slog.Error("endgame: missing arguments: expected 1 (board)")
		return NoResponse
	}

	game, err := convertBoard(args[0])
	if err != nil {
		slog.Error("endgame: convert board", "error", err)
		return NoResponse
	}

	winner := game.CheckWin()
	slog.Info("endgame check", "winner", winner)

	return map[string]any{"winner": string(winner)}
}

func convertBoard(board js.Value) (*gomoku.Game, error) {
	if !board.Truthy() {
		slog.Error("missing board field")
		return nil, errors.New("missing board field")
	}
	if board.Length() != gomoku.N {
		slog.Error("invalid board length", "length", board.Length())
		return nil, errors.New("invalid board length")
	}
	v := make([]string, gomoku.N)
	for r := range gomoku.N {
		v[r] = board.Index(r).String()
	}
	game := gomoku.Import(&gomoku.GameExport{Field: v})
	return game, nil
}

func main() {
	js.Global().Set("evaluate", js.FuncOf(evaluation))
	js.Global().Set("minimax", js.FuncOf(minimax))
	js.Global().Set("endgame", js.FuncOf(endgame))

	select {}
}
