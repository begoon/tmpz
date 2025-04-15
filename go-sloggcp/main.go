package main

import (
	"log/slog"
	"os"

	"github.com/vlad-tokarev/sloggcp"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stderr, &slog.HandlerOptions{
		ReplaceAttr: sloggcp.ReplaceAttr,
		AddSource:   true,
		Level:       slog.LevelDebug,
	}))
	slog.SetDefault(logger)
	slog.Info("aloha!")
}
