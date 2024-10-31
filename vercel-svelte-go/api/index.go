package api

import (
	"bytes"
	"embed"
	_ "embed"
	"encoding/json"
	"fmt"
	"io/fs"
	"net/http"
	"os"
	"strings"
)

func must[T any](v T, err error) T {
	if err != nil {
		panic(err)
	}
	return v
}

//go:embed static
var staticEmbedFS embed.FS

var staticFS = must(fs.Sub(staticEmbedFS, "static"))

const DATA = "window.__DATA__ = {}"

func indexDefault(r *http.Request) string {
	path := r.URL.Path
	if path == "/" {
		path = "/index.html"
	}
	if strings.HasSuffix(path, "/") {
		path += "index.html"
	}
	if !strings.Contains(path, ".") {
		path += "/index.html"
	}
	fmt.Printf("path: %s [%s]\n", path, r.URL.Path)
	return path
}

type pageData = struct {
	Path string      `json:"path"`
	Page string      `json:"page"`
	Data interface{} `json:"data"`
}

func loadData(path string) interface{} {
	if path == "/index.html" {
		return struct {
			Index interface{} `json:"index"`
		}{
			Index: "INDEX DATA",
		}
	}
	if path == "/a/index.html" {
		return struct {
			A interface{} `json:"a"`
		}{
			A: "A DATA",
		}
	}
	if path == "/b/index.html" {
		return struct {
			B interface{} `json:"b"`
		}{
			B: "B DATA",
		}
	}
	return struct{}{}
}

func Handler(w http.ResponseWriter, r *http.Request) {
	path := indexDefault(r)

	if !strings.HasSuffix(path, ".html") {
		fs := http.FS(staticFS)
		w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
		http.FileServer(fs).ServeHTTP(w, r)
		return
	}

	page := "pages" + path
	fmt.Printf("-> %s\n", page)

	content, err := fs.ReadFile(staticFS, page)
	if err != nil {
		http.Error(w, fmt.Sprintf("error read file: %s", err), http.StatusInternalServerError)
		return
	}

	fmt.Println("->", os.Getenv("COMMIT"))

	data := struct {
		Path   string              `json:"path"`
		Page   string              `json:"page"`
		Query  map[string][]string `json:"query"`
		Commit string              `json:"commit"`
		Data   interface{}         `json:"data"`
	}{
		Path:   path,
		Page:   page,
		Query:  r.URL.Query(),
		Commit: os.Getenv("COMMIT"),
		Data:   loadData(path),
	}

	b, err := json.Marshal(data)
	if err != nil {
		http.Error(w, fmt.Sprintf("error marshal json: %s", err), http.StatusInternalServerError)
		return
	}

	content = bytes.ReplaceAll(
		content, []byte(DATA),
		[]byte(fmt.Sprintf("window.__DATA__ = %s;", string(b))),
	)
	w.Header().Set("Content-Type", "text/html")
	w.Write(content)
}
