package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"google.golang.org/api/idtoken"
)

func main() {
	var (
		baseURL  string
		audience string
		path     string
		timeout  time.Duration
	)

	flag.StringVar(&baseURL, "url", "", "Base URL of the IAP-protected service (e.g. https://example.com)")
	flag.StringVar(&audience, "audience", "", "IAP OAuth client ID (e.g. xxx.apps.googleusercontent.com)")
	flag.StringVar(&path, "path", "/health", "Path to query (defaults to /health)")
	flag.DurationVar(&timeout, "timeout", 10*time.Second, "HTTP request timeout")
	flag.Parse()

	if baseURL == "" || audience == "" {
		flag.Usage()
		os.Exit(1)
	}

	targetURL := joinURL(baseURL, path)

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	client, err := idtoken.NewClient(ctx, audience)
	if err != nil {
		log.Fatalf("failed to create ID token client: %v", err)
	}
	client.Timeout = timeout

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, targetURL, nil)
	if err != nil {
		log.Fatalf("failed to create request: %v", err)
	}

	resp, err := client.Do(req)
	if err != nil {
		log.Fatalf("request failed: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatalf("failed to read response body: %v", err)
	}

	fmt.Printf("Status: %s\n", resp.Status)
	fmt.Printf("URL:    %s\n\n", targetURL)
	fmt.Println(string(body))
}

func joinURL(base, path string) string {
	if path == "" {
		return base
	}
	if !strings.HasPrefix(path, "/") {
		path = "/" + path
	}
	switch {
	case strings.HasSuffix(base, "/"):
		return strings.TrimRight(base, "/") + path
	default:
		return base + path
	}
}
