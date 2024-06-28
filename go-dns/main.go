package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"log/slog"
	"net/http"
	"os"
	"time"

	"cloud.google.com/go/storage"
)

var SHA string

func main() {
	h := slog.NewJSONHandler(os.Stderr, &slog.HandlerOptions{
		Level: slog.LevelDebug,
		ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
			if a.Key == slog.LevelKey {
				a.Key = "severity"
				return a
			}
			if a.Key == slog.MessageKey {
				a.Key = "message"
				return a
			}
			return a
		},
	})
	slog.SetDefault(slog.New(h))

	debug := os.Getenv("GODEBUG")
	fmt.Printf("GODEBUG=[%s]\n", debug)
	if debug == "" {
		os.Setenv("GODEBUG", "netdns=2")
		fmt.Printf("FORCED GODEBUG=[%s]\n", os.Getenv("GODEBUG"))
	}
	fmt.Printf("SHA=%v\n", SHA)

	http.HandleFunc("GET /z/{path...}", server)
	http.HandleFunc("GET /env", env)
	http.HandleFunc("GET /error", boom)
	http.HandleFunc("POST /action", action)

	fmt.Println("listening on :8000")
	slog.Info("listening on :8000")
	http.ListenAndServe(":8000", nil)
}

func server(w http.ResponseWriter, r *http.Request) {
	v := r.PathValue("path")
	debug := os.Getenv("GODEBUG")
	path := r.URL.Path
	fmt.Printf("GODEBUG=[%s] method=%s path=%s\n", debug, r.Method, path)
	ip := myip()
	fmt.Fprintf(w, "stored [%s] [%s] [%s] commit=%v $=[%s]\n", path, debug, ip, SHA, v)
	store(path)
	slog.Info("REQUEST", "path", path, "ip", ip, "v", v)
}

func action(w http.ResponseWriter, r *http.Request) {
	var v map[string]interface{}
	data, err := io.ReadAll(r.Body)
	if err != nil {
		fmt.Fprintf(w, "error reading body: %v", err)
		return
	}
	if err := json.Unmarshal(data, &v); err != nil {
		fmt.Fprintf(w, "error unmarshalling: %v", err)
		return
	}
	v["status"] = "alive"
	vv, err := json.MarshalIndent(v, "", "  ")
	fmt.Fprintf(w, string(vv))
	if err != nil {
		fmt.Fprintf(w, "error marshalling: %v", err)
		return
	}
	slog.Info("ACTION", "v", v)
}

func boom(w http.ResponseWriter, r *http.Request) {
	slog.Error("BOOM", "path", r.URL.Path, "reason", r.Header.Get("X-Forwarded-For"))
}

func env(w http.ResponseWriter, r *http.Request) {
	for _, e := range os.Environ() {
		fmt.Fprintf(w, "%s\n", e)
	}
	j, _ := json.MarshalIndent(os.Environ(), "", "  ")
	fmt.Fprintf(w, "%s\n", j)
}

func store(v string) {
	now := time.Now().Format(time.RFC3339)

	err := persist("dropzone", "dns/z-"+now+".txt", v)
	if err != nil {
		log.Fatalf("error saving: %v", err)
	}
	log.Println("saved", now, v)
}

func persist(bucket string, name string, v string) error {
	ctx := context.TODO()
	client, err := storage.NewClient(ctx)
	if err != nil {
		return err
	}
	w := client.Bucket(bucket).Object(name).NewWriter(ctx)
	defer func() {
		_ = w.Close()
	}()
	_, err = w.Write([]byte(v))
	client.Close()
	return err
}

func myip() string {
	url := "https://api.ipify.org"

	client := &http.Client{}

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		fmt.Println("error creating request:", err)
		return err.Error()
	}

	resp, err := client.Do(req)
	if err != nil {
		fmt.Println("error sending request:", err)
		return err.Error()
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		fmt.Println("unexpected status code:", resp.StatusCode)
		return fmt.Sprintf("unexpected status code: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Println("error reading response body:", err)
		return err.Error()
	}

	fmt.Printf("response [%s]\n", string(body))
	return string(body)
}
