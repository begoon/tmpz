package api

import (
	"embed"
	_ "embed"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
	"strings"
)

//go:embed static
var staticFS embed.FS

var tmpls *template.Template

//go:embed templates
var tmplFS embed.FS

func init() {
	var err error
	tmpls, err = template.ParseFS(tmplFS, "templates/*")
	if err != nil {
		log.Fatalf("error parsing templates: %v", err)
	}
}

func Handler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	if path == "/" {
		path = "/index.html"
	}
	fmt.Printf("path: %s\n", path)
	// ---
	if strings.HasPrefix(path, "/static") {
		fs := http.FS(staticFS)
		http.FileServer(fs).ServeHTTP(w, r)
		return
	}
	// ---
	data := map[string]interface{}{}
	for k, v := range r.URL.Query() {
		data[k] = v
	}
	for _, v := range os.Environ() {
		name, value, _ := strings.Cut(v, "=")
		data[name] = value
	}
	err := tmpls.ExecuteTemplate(w, path[1:], data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
