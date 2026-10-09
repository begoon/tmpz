package web

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
	"VERCEL_DEPLOYMENT_KEY": true,
	"VERCEL_ENV_ENC_KEY":    true,
}

func redact(s string) string {
	if len(s) <= 8 {
		return "..."
	}
	return s[:4] + "..." + s[len(s)-4:]
}

type variable struct {
	Name  string
	Label template.HTML // Name with matches of the filter wrapped in <mark>
	Value string
}

// highlight returns name as safe HTML with every case-insensitive occurrence
// of filter wrapped in a <mark> element. An empty filter marks nothing.
func highlight(name, filter string) template.HTML {
	if filter == "" {
		return template.HTML(template.HTMLEscapeString(name))
	}
	var b strings.Builder
	lower := strings.ToLower(name)
	for {
		i := strings.Index(lower, filter)
		if i < 0 {
			b.WriteString(template.HTMLEscapeString(name))
			break
		}
		end := i + len(filter)
		b.WriteString(template.HTMLEscapeString(name[:i]))
		b.WriteString("<mark>")
		b.WriteString(template.HTMLEscapeString(name[i:end]))
		b.WriteString("</mark>")
		name, lower = name[end:], lower[end:]
	}
	return template.HTML(b.String())
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
		vars = append(vars, variable{name, highlight(name, filter), value})
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
		name = "variables"
	}
	err := tmpls.ExecuteTemplate(w, name, data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
