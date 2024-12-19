package main

import (
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
)

func handler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello, World!")
}

func configureLogging() {
	programLevel := new(slog.LevelVar)

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: programLevel}))
	slog.SetDefault(logger)

	if os.Getenv("DEBUG") != "" {
		programLevel.Set(slog.LevelDebug)
	}
}

func main() {
	configureLogging()

	http.HandleFunc("/", handler)

	addr := "localhost:8000"
	server := &http.Server{Addr: addr}

	done := make(chan struct{})
	go func(done chan<- struct{}) {
		slog.Debug("server.ListenAndServe", "addr", addr)
		err := server.ListenAndServe()
		if err != nil {
			slog.Debug("server.ListenAndServe", "error", err)
		}
		close(done)
	}(done)

	r, err := http.Get("http://" + addr)
	if err != nil {
		slog.Error("http.Get failed", "error", err)
		return
	}
	defer r.Body.Close()
	t, err := io.ReadAll(r.Body)
	if err != nil {
		slog.Error("io.ReadAll failed", "error", err)
		return
	}
	fmt.Println(string(t))
	err = server.Shutdown(nil)
	if err != nil {
		slog.Error("server.Shutdown failed", "error", err)
		return
	}
	<-done
}
