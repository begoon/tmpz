package main

import (
	"context"
	"log"
	"os"
	"runtime/debug"
	"time"

	"cloud.google.com/go/logging"
	"github.com/google/uuid"
	"github.com/joho/godotenv"
)

func main() {
	godotenv.Load()

	project := os.Getenv("PROJECT_ID")
	if project == "" {
		log.Fatal("PROJECT_ID environment variable is not set")
	}

	ctx := context.Background()

	client, err := logging.NewClient(ctx, "iproov-chiro")
	if err != nil {
		log.Fatalf("initialize logging client: %v", err)
	}
	defer func() {
		if err := client.Close(); err != nil {
			log.Fatalf("close logging client: %v", err)
		}
	}()

	l := client.Logger("go-cli",
		logging.SourceLocationPopulation(logging.AlwaysPopulateSourceLocation),
		logging.CommonLabels(map[string]string{
			"appication": "go-application",
			"version":    "1.0.0",
			"env":        "production",
		}),
	)
	stackTrace := debug.Stack()
	l.Log(logging.Entry{
		Payload: map[string]string{
			"message":     "abc-xyz " + time.Now().Format(time.RFC3339),
			"a":           "A",
			"stack_trace": string(stackTrace),
		},
		Severity:  logging.Error,
		Labels:    map[string]string{"extra": "extra-" + time.Now().Format(time.RFC3339)},
		Timestamp: time.Now(),
		Trace:     "trace|" + uuid.New().String(),
		SpanID:    "span|" + uuid.New().String(),
	})
}
