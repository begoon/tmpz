package web

import (
	"bytes"
	_ "embed"
	"html/template"
	"net/http"
	"strings"

	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/ast"
	"github.com/yuin/goldmark/parser"
	"github.com/yuin/goldmark/text"
	"github.com/yuin/goldmark/util"
)

// readmeSource is a vendored copy of https://github.com/begoon/begoon/blob/main/README.md.
//
//go:embed content/README.md
var readmeSource []byte

// readmeBase is where relative links in the README resolve to.
const readmeBase = "https://github.com/begoon/begoon/blob/main/"

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

// readmeHTML is the README rendered once at startup.
var readmeHTML = func() template.HTML {
	md := goldmark.New(goldmark.WithParserOptions(
		parser.WithASTTransformers(util.Prioritized(absoluteLinks{}, 100)),
	))
	var buf bytes.Buffer
	if err := md.Convert(readmeSource, &buf); err != nil {
		panic(err)
	}
	// Colour the star-count glyphs like GitHub does.
	html := strings.ReplaceAll(buf.String(), "★", `<span class="star">★</span>`)
	return template.HTML(html)
}()

func meHandler(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Cache-Control", "public, s-maxage=600, stale-while-revalidate=3600")
	render(w, "me.html", "me.html", map[string]any{"Content": readmeHTML, "Version": version})
}
