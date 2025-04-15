package main

import (
	"context"
	"log/slog"

	_ "github.com/chainguard-dev/clog/gcp/init"

	"github.com/chainguard-dev/clog"
)

func main() {
	log := clog.New(slog.Default().Handler()).With("a", "b")
	ctx := clog.WithLogger(context.Background(), log)

	f(ctx)
}

func f(ctx context.Context) {
	log := clog.FromContext(ctx)
	log.Info("in f")

	ctx = clog.WithLogger(ctx, log.With("f", "hello"))
	g(ctx)
}

func g(ctx context.Context) {
	log := clog.FromContext(ctx)
	log.Info("in g")

	clog.ErrorContext(ctx, "asdf")
}
