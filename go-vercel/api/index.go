package api

import (
	"embed"
	_ "embed"
	"fmt"
	"io/fs"
	"log"
	"net/http"
)

//go:embed html
var site embed.FS
var content fs.FS

func init() {
	var err error
	content, err = fs.Sub(site, "html")
	if err != nil {
		log.Fatalf("error getting site fs: %v", err)
	}
}

func Handler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	if path == "/" {
		path = "/index.html"
	}
	fmt.Printf("path: %s\n", path)
	fs := http.FS(content)
	http.FileServer(fs).ServeHTTP(w, r)
}
