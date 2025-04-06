package main

import (
	"net/http"
	"os"
	"runtime/debug"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

type SeverityHook struct{}

func (h SeverityHook) Run(e *zerolog.Event, level zerolog.Level, msg string) {
	e.Str("severity", level.String())
}

func main() {
	log.Logger = log.Hook(SeverityHook{})

	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	zerolog.SetGlobalLevel(zerolog.InfoLevel)

	log.Info().Msg("starting...")

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("OK"))
	})
	http.HandleFunc("/error", func(w http.ResponseWriter, r *http.Request) {
		log.Error().Int("i", 100).Msg("error message")
	})
	http.HandleFunc("/panic/message", func(w http.ResponseWriter, r *http.Request) {
		stack := string(debug.Stack())
		log.Error().Int("i", 100).
			Str("stack_trace", stack).
			Msg("error " + time.Now().Format(time.RFC3339))
	})
	http.HandleFunc("/panic/bare", func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				log.Error().Int("i", 100).Msg("bare panic message " + string(debug.Stack()))
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
				return
			}
		}()
		panic("panic!")
	})
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	err := http.ListenAndServe(":"+port, nil)
	if err != nil {
		log.Fatal().Err(err).Msg("start server")
	}
}
