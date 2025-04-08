package main

import (
	"context"
	"errors"
	"log"
	"os"
	"runtime/debug"
	"time"

	"cloud.google.com/go/errorreporting"
	"cloud.google.com/go/errorreporting/apiv1beta1/errorreportingpb"
	"cloud.google.com/go/logging"
	"github.com/google/uuid"
	"github.com/joho/godotenv"
	"google.golang.org/protobuf/encoding/protojson"
)

func main() {
	godotenv.Load()

	project := os.Getenv("PROJECT")
	if project == "" {
		log.Fatal("PROJECT environment variable is not set")
	}
	log.Printf("project: %s", project)

	if len(os.Args) > 1 && os.Args[1] == "error" {
		errorClient, err := errorreporting.NewClient(context.Background(), project, errorreporting.Config{
			ServiceName:    "dev-api",
			ServiceVersion: "1.0.0",
			OnError: func(err error) {
				log.Fatalf("report error: %v", err)
			},
		})
		defer func() {
			if err := errorClient.Close(); err != nil {
				log.Fatalf("close error client: %v", err)
			}
		}()
		if err != nil {
			log.Fatalf("initialize error client: %v", err)
		}
		errorClient.Report(errorreporting.Entry{
			Error: errors.New("synthetic error / panic"),
			Stack: debug.Stack(),
			User:  os.Getenv("USER"),
		})
		errorClient.Report(errorreporting.Entry{
			Error: errors.New("synthetic error / message"),
			User:  os.Getenv("USER"),
		})
		return
	}
	ctx := context.Background()

	client, err := logging.NewClient(ctx, project)
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
	message := "panic: synthetic " + time.Now().Format(time.RFC3339)
	serviceContext, err := protojson.Marshal(&errorreportingpb.ServiceContext{
		Service: "dev-api",
		Version: "1.0.0",
	})
	if err != nil {
		log.Fatalf("marshal service context: %v", err)
	}
	l.Log(logging.Entry{
		Payload: map[string]string{
			"message":        message,
			"a":              "A",
			"stack_trace":    message + "\n" + string(stackTrace),
			"@type":          "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent",
			"serviceContext": string(serviceContext),
		},
		Severity: logging.Error,
		Labels: map[string]string{
			"extra": "extra-" + time.Now().Format(time.RFC3339),
		},
		Timestamp: time.Now(),
		Trace:     "trace|" + uuid.New().String(),
		SpanID:    "span|" + uuid.New().String(),
	})
}
