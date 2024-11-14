package main

import (
	"bytes"
	"fmt"
	"html/template"
	"log"
	"math"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type Document struct {
	Name  string
	Path  string
	Text  string
	Score float64
}

var (
	documents  []Document
	tfidfIndex map[string]map[string]float64
)

func loadDocuments() {
	rootDir := "data/"

	skip := func(v string) bool {
		return !strings.HasPrefix(v, rootDir)
	}

	err := filepath.Walk(rootDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			log.Printf("error accessing path %q: %v\n", path, err)
			return err
		}
		if !info.IsDir() && !skip(path) {
			content, err := os.ReadFile(path)
			if err != nil {
				log.Printf("error reading file %s: %v", path, err)
				return nil
			}
			text := strings.ToLower(string(content))
			relativePath := strings.TrimPrefix(path, rootDir)
			documents = append(documents, Document{Name: info.Name(), Path: relativePath, Text: text, Score: 0})
		}
		return nil
	})
	if err != nil {
		log.Fatalf("error walking the path %q: %v\n", rootDir, err)
	}
	fmt.Printf("loaded %d documents\n", len(documents))
}

func buildIndex() {
	tfidfIndex = make(map[string]map[string]float64)
	number := len(documents)

	for _, document := range documents {
		words := strings.Fields(document.Text)
		wordCount := make(map[string]int)

		for _, word := range words {
			wordCount[word]++
		}

		for word, count := range wordCount {
			if tfidfIndex[word] == nil {
				tfidfIndex[word] = make(map[string]float64)
			}
			tf := float64(count) / float64(len(words))
			tfidfIndex[word][document.Name] = tf
		}
	}

	for word, documentMap := range tfidfIndex {
		frequency := float64(len(documentMap))
		idf := math.Log(float64(number) / (1 + frequency))
		for document, tf := range documentMap {
			tfidfIndex[word][document] = tf * idf
		}
	}
}

func search(query string) []Document {
	words := strings.Fields(strings.ToLower(query))
	scores := make(map[string]float64)

	for _, word := range words {
		for document, tfidf := range tfidfIndex[word] {
			scores[document] += tfidf
		}
	}

	var results []Document
	for _, document := range documents {
		if score, found := scores[document.Name]; found && score > 0 {
			results = append(results, Document{
				Name:  document.Name,
				Path:  document.Path,
				Text:  document.Text,
				Score: score,
			})
		}
	}

	sort.Slice(results, func(i, j int) bool {
		return results[i].Score > results[j].Score
	})

	return results
}

func searchHandler(w http.ResponseWriter, r *http.Request) {
	htmx := r.Header.Get("HX-Request") != ""

	var tmpl *template.Template
	context := struct {
		Query   string
		Results []Document
	}{Query: r.URL.Query().Get("q")}

	if context.Query != "" {
		context.Results = search(context.Query)
	}

	templName := "search.html"
	if htmx {
		templName = "results.html"
	}
	tmpl = template.Must(template.ParseFiles("templates/" + templName))
	tmpl.Execute(w, context)
}

func fileHandler(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query().Get("q")
	root := "data/"
	path := root + r.URL.Path[1:]
	content, err := os.ReadFile(path)
	if q != "" {
		content = bytes.ReplaceAll(content, []byte(q), []byte("<mark>"+q+"</mark>"))
		isHTML := strings.HasSuffix(path, ".html")
		if !isHTML {
			content = []byte("<pre>" + string(content) + "</pre>")
			w.Header().Set("Content-Type", "text/html")
		}
	}
	if err != nil {
		http.Error(w, "file not found", http.StatusNotFound)
		return
	}
	w.Write(content)
}

func main() {
	loadDocuments()
	buildIndex()

	http.HandleFunc("GET /{$}", searchHandler)
	http.HandleFunc("/{path...}", fileHandler)

	fmt.Println("listening on :8000")
	http.ListenAndServe(":8000", nil)
}
