package main

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"gomoku/gomoku"
)

type Move struct {
	R int `json:"r"`
	C int `json:"c"`
}

type EvalRequest struct {
	Move  *Move    `json:"move"`
	Board []string `json:"board"`
}

type EvalResponse struct {
	Value int `json:"value"`
}

type MinimaxRequest struct {
	Depth int      `json:"depth"`
	Board []string `json:"board"`
}

type MinimaxResponse struct {
	Move Move `json:"move"`
}

type EndgameRequest struct {
	Board []string `json:"board"`
}

type EndgameResponse struct {
	Winner string `json:"winner"`
}

func server() {
	http.Handle("/", http.FileServer(http.Dir("site")))
	http.HandleFunc("POST /eval", evalHandler)
	http.HandleFunc("POST /minimax", minimaxHandler)
	http.HandleFunc("POST /end", endgameHandler)
	http.ListenAndServe(":8000", nil)
}

func minimaxHandler(w http.ResponseWriter, r *http.Request) {
	slog.Info("minimax")

	request := MinimaxRequest{}
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		slog.Error("decode minimax request", "error", err)
		http.Error(w, "invalid minimax request", http.StatusBadRequest)
		return
	}

	export := gomoku.GameExport{Field: request.Board}
	game := gomoku.Import(&export)

	gomoku.PrintBoard(game)

	depth := request.Depth
	if depth <= 0 {
		depth = 2
	}
	slog.Info("minimax", "depth", depth)

	value, move := game.Minimax(depth)
	slog.Info("minimax result", "value", value, "move", move)

	{
		r, c := move.Unpack()
		minimaxResponse := MinimaxResponse{Move: Move{R: r, C: c}}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(minimaxResponse)
	}
}

func evalHandler(w http.ResponseWriter, r *http.Request) {
	slog.Info("evaluation")

	request := EvalRequest{}
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		slog.Error("decode evaluation request", "error", err)
		http.Error(w, "invalid request", http.StatusBadRequest)
		return
	}

	export := gomoku.GameExport{Field: request.Board}
	game := gomoku.Import(&export)

	if request.Move != nil {
		move := gomoku.MoveAt(request.Move.R, request.Move.C)
		slog.Info("evaluate", "move", move)
		game.Place(move, gomoku.Human)
	}
	gomoku.PrintBoard(game)

	value := game.Evaluate()
	slog.Info("evaluation", "value", value)

	evalResponse := EvalResponse{Value: value}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(evalResponse)
}

func endgameHandler(w http.ResponseWriter, r *http.Request) {
	slog.Info("endgame check")

	request := EndgameRequest{}
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		slog.Error("decode endgame request", "error", err)
		http.Error(w, "invalid request", http.StatusBadRequest)
		return
	}

	export := gomoku.GameExport{Field: request.Board}
	game := gomoku.Import(&export)

	gomoku.PrintBoard(game)

	winner := game.CheckWin()
	slog.Info("endgame check", "winner", winner)

	endgameResponse := EndgameResponse{Winner: string(winner)}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(endgameResponse)
}
