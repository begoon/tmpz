package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"cloud.google.com/go/storage"
)

func main() {
	debug := os.Getenv("GODEBUG")
	fmt.Printf("GODEBUG=[%s]\n", debug)
	if debug == "" {
		os.Setenv("GODEBUG", "netdns=2")
		fmt.Printf("FORCED GODEBUG=[%s]\n", os.Getenv("GODEBUG"))
	}

	http.HandleFunc("GET /x/{path...}", server)
	http.HandleFunc("GET /env", env)
	fmt.Println("listening on :8000")
	http.ListenAndServe(":8000", nil)
}

func server(w http.ResponseWriter, r *http.Request) {
	v := r.PathValue("path")
	debug := os.Getenv("GODEBUG")
	path := r.URL.Path
	fmt.Printf("GODEBUG=[%s] method=%s path=%s\n", debug, r.Method, path)
	ip := myip()
	fmt.Fprintf(w, "stored [%s] [%s] [%s] $=[%s]\n", path, debug, ip, v)
	store(path)
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
