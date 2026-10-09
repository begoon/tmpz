package web

import (
	"bytes"
	"context"
	"fmt"
	"html/template"
	"io"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/ast"
	"github.com/yuin/goldmark/parser"
	"github.com/yuin/goldmark/text"
	"github.com/yuin/goldmark/util"
)

const (
	readmeURL  = "https://raw.githubusercontent.com/begoon/begoon/main/README.md"
	readmeBase = "https://github.com/begoon/begoon/blob/main/"
	readmeTTL  = 10 * time.Minute
)

// absoluteLinks rewrites relative link destinations in the README so they
// keep pointing into the GitHub repository when served from this site.
type absoluteLinks struct{}

func (absoluteLinks) Transform(doc *ast.Document, _ text.Reader, _ parser.Context) {
	ast.Walk(doc, func(n ast.Node, entering bool) (ast.WalkStatus, error) {
		if !entering {
			return ast.WalkContinue, nil
		}
		link, ok := n.(*ast.Link)
		if !ok {
			return ast.WalkContinue, nil
		}
		dest := string(link.Destination)
		if dest == "" || strings.HasPrefix(dest, "#") || strings.Contains(dest, "://") {
			return ast.WalkContinue, nil
		}
		link.Destination = []byte(readmeBase + dest)
		return ast.WalkContinue, nil
	})
}

var markdown = goldmark.New(goldmark.WithParserOptions(
	parser.WithASTTransformers(util.Prioritized(absoluteLinks{}, 100)),
))

var readme struct {
	sync.Mutex
	html    template.HTML
	fetched time.Time
}

// readmeHTML returns the rendered README, refetching it from GitHub when the
// cached copy is older than readmeTTL. A failed refresh serves the stale copy
// when there is one.
func readmeHTML(ctx context.Context) (template.HTML, error) {
	readme.Lock()
	defer readme.Unlock()
	if readme.html != "" && time.Since(readme.fetched) < readmeTTL {
		return readme.html, nil
	}
	html, err := fetchReadme(ctx)
	if err != nil {
		if readme.html != "" {
			return readme.html, nil
		}
		return "", err
	}
	readme.html, readme.fetched = html, time.Now()
	return html, nil
}

func fetchReadme(ctx context.Context) (template.HTML, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, readmeURL, nil)
	if err != nil {
		return "", err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("fetching README: %s", resp.Status)
	}
	source, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return "", err
	}
	var buf bytes.Buffer
	if err := markdown.Convert(source, &buf); err != nil {
		return "", err
	}
	return template.HTML(buf.String()), nil
}

func meHandler(w http.ResponseWriter, r *http.Request) {
	content, err := readmeHTML(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}
	w.Header().Set("Cache-Control", "public, s-maxage=600, stale-while-revalidate=3600")
	render(w, "me.html", "me.html", map[string]any{"Content": content, "Version": version})
}
