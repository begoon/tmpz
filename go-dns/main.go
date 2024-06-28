package main

import (
	"context"
	"fmt"
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
		os.Setenv("GODEBUG", "netdns=1")
		fmt.Printf("FORCED GODEBUG=[%s]\n", os.Getenv("GODEBUG"))
	}

	http.HandleFunc("/", server)
	fmt.Println("listening on :8000")
	http.ListenAndServe(":8000", nil)
}

func server(w http.ResponseWriter, r *http.Request) {
	debug := os.Getenv("GODEBUG")
	path := r.URL.Path
	fmt.Printf("GODEBUG=[%s] method=%s path=%s\n", debug, r.Method, path)
	fmt.Fprintf(w, "storing [%s] [%s]", path, debug)
	store(path)
}

func store(v string) {
	now := time.Now().Format(time.RFC3339)

	err := StorageSave("dropzone", "dns/z-"+now+".txt", v)
	if err != nil {
		log.Fatalf("error saving: %v", err)
	}
	log.Println("saved", now, v)
}

func StorageSave(bucket string, name string, v string) error {
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
