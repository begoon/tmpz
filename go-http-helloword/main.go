package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
)

func handler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello, World!")
}

func main() {
	http.HandleFunc("/", handler)
	go func() {
		err := http.ListenAndServe(":8000", nil)
		if err != nil {
			log.Fatalf("http.ListenAndServe failed: %v", err)
		}
	}()
	r, err := http.Get("http://localhost:8000/")
	if err != nil {
		log.Fatalf("http.Get failed: %v", err)
	}
	defer r.Body.Close()
	t, err := io.ReadAll(r.Body)
	if err != nil {
		log.Fatalf("io.ReadAll failed: %v", err)
	}
	fmt.Println(string(t))
}
