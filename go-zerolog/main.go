package main

import (
	"log/slog"
	"os"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func main() {
	log.Info().
		Str("s", "str").
		Dict("dict", zerolog.Dict().
			Int("n", 1)).
		Msg("aloha!")
	slog.Info("aloha!", slog.Group("dict", slog.Int("n", 1)), "b", 2, "s", "str", "a", 1)

	slogJSON := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	slogJSON.Info("aloha!", slog.Group("dict", slog.Int("n", 1)), "b", 2, "s", "str", "a", 1)
}
