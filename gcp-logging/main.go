package main

import (
	"os"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

type SeverityHook struct{}

func (h SeverityHook) Run(e *zerolog.Event, level zerolog.Level, msg string) {
	e.Str("severity", level.String())
}

func main() {
	log.Logger = log.Hook(SeverityHook{})

	log.Info().Msg("INFO message")
	log.Debug().Msg("DEBUG message")
	log.Warn().Msg("WARN message")
	log.Error().Msg("ERROR message")

	log.Info().Any("env", os.Environ()).Send()
}
