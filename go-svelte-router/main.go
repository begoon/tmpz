package main

import (
	"embed"
	_ "embed"
	"encoding/json"
	"fmt"
	"io/fs"
	"net/http"
	"os"
	"strings"
)

//go:embed dist
var embedFS embed.FS

func must[T any](a T, err error) T {
	if err != nil {
		panic(err)
	}
	return a
}

//go:embed VERSION.txt
var version string

//go:embed TAG.txt
var tag string

func main() {
	version = strings.TrimSpace(version)
	tag = strings.TrimSpace(tag)

	http.Handle("/", http.FileServer(http.FS(must(fs.Sub(embedFS, "dist")))))
	http.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		health := struct {
			Version string `json:"version"`
			Tag     string `json:"tag"`
		}{Version: version, Tag: tag}
		err := json.NewEncoder(w).Encode(health)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
	})

	port := "8000"
	if os.Getenv("PORT") != "" {
		port = os.Getenv("PORT")
	}

	fmt.Println("listening on " + port)
	http.ListenAndServe(":"+port, nil)
}
