package api

import (
	"bytes"
	"embed"
	_ "embed"
	"encoding/json"
	"fmt"
	"io/fs"
	"net/http"
	"strings"
	"time"
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

	data := struct {
		Path string    `json:"path"`
		Page string    `json:"page"`
		When time.Time `json:"when"`
		IP   string    `json:"ip"`
	}{
		Path: path,
		Page: page,
		When: time.Now(),
	}

	if path == "/index.html" {
		data.IP = r.RemoteAddr
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
