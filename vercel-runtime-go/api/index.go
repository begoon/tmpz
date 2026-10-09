package api

import (
	"crypto/sha256"
	"embed"
	"encoding/hex"
	"fmt"
	"html/template"
	"net/http"
	"os"
	"sort"
	"strings"
)

//go:embed static
var staticFS embed.FS

//go:embed templates
var tmplFS embed.FS

var tmpls = template.Must(template.New("").Funcs(template.FuncMap{"static": staticURL}).ParseFS(tmplFS, "templates/*"))

// staticURL returns the URL of an embedded static file with a content hash
// appended, so the immutable CDN cache is bypassed whenever the file changes.
func staticURL(name string) string {
	content, err := staticFS.ReadFile("static/" + name)
	if err != nil {
		return "/static/" + name
	}
	sum := sha256.Sum256(content)
	return "/static/" + name + "?v=" + hex.EncodeToString(sum[:8])
}

var secretEnv = map[string]bool{
	"AWS_ACCESS_KEY_ID":     true,
	"AWS_SECRET_ACCESS_KEY": true,
	"AWS_SESSION_TOKEN":     true,
}

func redact(s string) string {
	if len(s) <= 8 {
		return "..."
	}
	return s[:4] + "..." + s[len(s)-4:]
}

type variable struct {
	Name  string
	Value string
}

// variables returns the environment, with secrets redacted, sorted by name
// and filtered to names containing filter (case-insensitive).
func variables(filter string) []variable {
	filter = strings.ToLower(filter)
	var vars []variable
	for _, v := range os.Environ() {
		name, value, _ := strings.Cut(v, "=")
		if !strings.Contains(strings.ToLower(name), filter) {
			continue
		}
		if secretEnv[name] {
			value = redact(value)
		}
		vars = append(vars, variable{name, value})
	}
	sort.Slice(vars, func(i, j int) bool { return vars[i].Name < vars[j].Name })
	return vars
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
		w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
		http.FileServer(fs).ServeHTTP(w, r)
		return
	}
	// ---
	q := r.URL.Query().Get("q")
	data := map[string]any{"Query": q, "Vars": variables(q)}
	name := path[1:]
	if path == "/variables" {
		name = "vars"
	}
	err := tmpls.ExecuteTemplate(w, name, data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
