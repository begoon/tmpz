package main

import (
	"context"
	"log"
	"log/slog"
	"os"
	"path/filepath"
)

type name struct{}

func main() {
	l := log.New(log.Writer(), "PREFIX | ", log.LstdFlags|log.Lshortfile|log.Lmsgprefix)
	l.Println("ha?")
	l.Output(1, "ha?")

	ctx := context.Background()
	ctx = context.WithValue(ctx, name{}, "me")

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		AddSource: true,
		ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
			if a.Key == slog.SourceKey {
				source := a.Value.Any().(*slog.Source)
				source.File = filepath.Base(source.File)
			}
			return a
		},
	}))

	slog.SetDefault(logger)

	logger.InfoContext(ctx, "start", "user", "alice", slog.Group("context", "name", ctx.Value(name{})))
}
