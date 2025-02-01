package main

import (
	"embed"
	_ "embed"
	"fmt"
	"io/fs"
	"net/http"
	"os"
)

//go:embed dist
var embedFS embed.FS

func must[T any](a T, err error) T {
	if err != nil {
		panic(err)
	}
	return a
}

func main() {
	http.Handle("/", http.FileServer(http.FS(must(fs.Sub(embedFS, "dist")))))

	port := "8000"
	if os.Getenv("PORT") != "" {
		port = os.Getenv("PORT")
	}

	fmt.Println("listening on " + port)
	http.ListenAndServe(":"+port, nil)
}
