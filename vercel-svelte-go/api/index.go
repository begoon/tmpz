package api

import (
	"bytes"
	"context"
	"embed"
	_ "embed"
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"io/fs"
	"log"
	"net/http"
	"os"
	"runtime/debug"
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

//go:embed COMMIT.txt
var commit string

const DATA = "window.__DATA__ = {}"

type PageLoader func(w http.ResponseWriter, r *http.Request) *Page

type Page struct {
	ID     string      `json:"id"`
	Static bool        `json:"static"`
	Data   interface{} `json:"data"`
}

var assets = make(map[string]bool)

var mux = http.NewServeMux()

func indexAssets() {
	err := fs.WalkDir(staticFS, ".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.Type().IsRegular() {
			assets["/"+path] = true
			log.Printf("- asset: %s\n", path)
		}
		return nil
	})
	if err != nil {
		log.Fatalf("error indexing assets: %s", err)
	}
	log.Printf("indexed %d assets\n", len(assets))
}

func init() {
	indexAssets()

	mux.HandleFunc("POST /report", func(w http.ResponseWriter, r *http.Request) {
		message := r.FormValue("message")
		log.Printf("REPORT: %s\n", message)
		if err := TelegramNotification(message); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		http.Redirect(w, r, "/a/reported", http.StatusSeeOther)
	})

	mux.HandleFunc("GET /ping/{args...}", func(w http.ResponseWriter, r *http.Request) {
		args := r.PathValue("args")
		log.Printf("HEAD /ping: %#v\n", args)
		w.WriteHeader(http.StatusOK)
		if args != "" {
			w.Write([]byte(args))
		} else {
			w.Write([]byte("alive"))
		}
	})

	mux.HandleFunc("GET /paused/{seconds...}", func(w http.ResponseWriter, r *http.Request) {
		seconds := r.PathValue("seconds")
		n, err := time.ParseDuration(seconds)
		if err != nil {
			http.Error(w, fmt.Errorf("error parsing duration: %w", err).Error(), http.StatusBadRequest)
			return
		}

		ctx, cancel := context.WithTimeout(context.Background(), n)
		defer cancel()

		req, err := http.NewRequestWithContext(ctx, "GET", "https://httpbin.org/delay/3", nil)
		if err != nil {
			http.Error(w, fmt.Errorf("error creating request: %w", err).Error(), http.StatusInternalServerError)
			return
		}

		client := &http.Client{}
		resp, err := client.Do(req)
		if err != nil {
			http.Error(w, fmt.Errorf("error dialing httpbin: %w", err).Error(), http.StatusInternalServerError)
			return
		}
		defer resp.Body.Close()

		http.Error(w, "OK", http.StatusOK)
	})

	mux.HandleFunc("GET /endpoint/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		userID := r.PathValue("id")
		log.Printf("\t> USER: %#v\n", userID)
		fmt.Fprintf(w, "user=%s", userID)
	})

	mux.HandleFunc("GET /endpoint/click/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		log.Printf("\t> CLICK: %#v\n", id)
	})

	mux.HandleFunc("GET /endpoint/public-ip", func(w http.ResponseWriter, r *http.Request) {
		ipfy := "https://api.ipify.org?format=text"

		resp, err := http.Get(ipfy)
		if err != nil {
			http.Error(w, fmt.Errorf("error dialing %s: %w", ipfy, err).Error(), http.StatusInternalServerError)
			return
		}
		defer resp.Body.Close()

		b, err := io.ReadAll(resp.Body)
		if err != nil {
			http.Error(w, fmt.Errorf("error reading response: %w", err).Error(), http.StatusInternalServerError)
			return
		}

		response := struct {
			IP string `json:"ip"`
		}{IP: string(b)}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)

		if err := json.NewEncoder(w).Encode(response); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}

		time.Sleep(1 * time.Second)
	})

	// pages

	mux.HandleFunc("GET /{$}", RenderPage(func(w http.ResponseWriter, r *http.Request) *Page {
		return &Page{
			ID: "/",
			Data: map[string]string{
				"DATA":   "ROOT DATA (*)",
				"COMMIT": commit,
			},
		}
	}))

	mux.HandleFunc("GET /a/{name}", RenderPage(func(w http.ResponseWriter, r *http.Request) *Page {
		name := r.PathValue("name")
		return &Page{
			ID: "/a",
			Data: map[string]string{
				"DATA": "A DATA (')",
				"NAME": name,
			},
		}
	}))

	mux.HandleFunc("GET /b/{args...}", RenderPage(func(w http.ResponseWriter, r *http.Request) *Page {
		args := r.PathValue("args")
		if args == "error" {
			panic("induced panic")
		}
		return &Page{
			ID: "/b",
			Data: map[string]string{
				"DATA": "B DATA (')",
				"ARGS": args,
			},
		}
	}))

	mux.HandleFunc("GET /cms", RenderPage(func(w http.ResponseWriter, r *http.Request) *Page {
		return &Page{
			ID:     "/cms",
			Static: true,
			Data: map[string]string{
				"DATA": "CMS",
			},
		}
	}))

	mux.HandleFunc("GET /z", RenderPage(func(w http.ResponseWriter, r *http.Request) *Page {
		return &Page{
			ID: "/",
			Data: map[string]string{
				"DATA": "A/Z",
			},
		}
	}))
}

func RenderPage(loader PageLoader) func(w http.ResponseWriter, r *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		user := r.Context().Value("user").(string)

		page := loader(w, r)
		page.Data.(map[string]string)["USER"] = user

		log.Printf("PAGE %s\n", page.ID)
		render(page, w, r)
	}
}

func recoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				log.Printf("PANIC: %s %s\n", err, debug.Stack())
				http.Error(w, fmt.Sprintf("panic: %s", err), http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func basicAuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/z") {
			user, pass, ok := r.BasicAuth()
			if !ok || user != "wheel" || pass != "raxxla" {
				w.Header().Set("WWW-Authenticate", `Basic realm="Restricted"`)
				http.Error(w, "unauthorized", http.StatusUnauthorized)
				return
			}
			r = r.WithContext(context.WithValue(r.Context(), "user", user))
		} else {
			r = r.WithContext(context.WithValue(r.Context(), "user", "anonymous"))
		}
		next.ServeHTTP(w, r)
	})
}

type Middleware func(http.HandlerFunc) http.HandlerFunc

type responseWriterWrapper struct {
	http.ResponseWriter
	statusCode int
	written    int
}

func (w *responseWriterWrapper) WriteHeader(statusCode int) {
	w.statusCode = statusCode
	w.ResponseWriter.WriteHeader(statusCode)
}

func (w *responseWriterWrapper) Write(b []byte) (int, error) {
	n, err := w.ResponseWriter.Write(b)
	w.written += n
	return n, err
}

func Handler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path

	ww := &responseWriterWrapper{ResponseWriter: w, statusCode: http.StatusOK}

	started := time.Now()
	log.Printf("REQUEST: %s %s\n", r.Method, path)
	defer func() {
		log.Printf("RESPONSE: %d %d %s\n", ww.statusCode, ww.written, time.Since(started))
	}()

	if assets[path] {
		w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
		log.Printf("STATIC: %s\n", path)
		http.FileServerFS(staticFS).ServeHTTP(ww, r)
		return
	}

	basicAuthMiddleware(recoveryMiddleware(mux)).ServeHTTP(ww, r)
}

func render(page *Page, w http.ResponseWriter, r *http.Request) {
	path := page.ID
	if !strings.HasSuffix(path, "/") {
		path += "/"
	}
	path += "index.html"
	log.Printf("RENDER: %s [%s]\n", path, r.URL.Path)

	if page.Static {
		path = path[1:]
	} else {
		path = "pages" + path
	}

	content, err := fs.ReadFile(staticFS, path)
	if err != nil {
		http.Error(w, fmt.Sprintf("error read page file: %s", err), http.StatusInternalServerError)
		return
	}

	content = bytes.Replace(content, []byte("{}"), []byte("{{ . }}"), 1)

	w.Header().Set("Content-Type", "text/html")
	t := template.Must(template.New("page").Parse(string(content)))

	log.Printf(" > PAGE DATA: %#v\n", page.Data)
	err = t.Execute(w, page)
	if err != nil {
		http.Error(w, fmt.Sprintf("error execute template: %s", err), http.StatusInternalServerError)
		return
	}
}

const TelegramAPI = "https://api.telegram.org/bot%s/%s"

func TelegramCommand(cmd string, payload interface{}) error {
	log.Printf("TELEGRAM: %s %v\n", cmd, payload)
	url := fmt.Sprintf(TelegramAPI, os.Getenv("TELEGRAM_BOT_TOKEN"), cmd)
	log.Printf("TELEGRAM URL: %s\n", url)

	b, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("error marshal telegram payload: %w", err)
	}
	resp, err := http.Post(url, "application/json", bytes.NewReader(b))
	if err != nil {
		return fmt.Errorf("error send telegram request: %w", err)
	}
	defer resp.Body.Close()
	log.Printf("TELEGRAM RESPONSE STATUS: %s\n", resp.Status)

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("error telegram response: %s", resp.Status)
	}

	data := make(map[string]interface{})
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return fmt.Errorf("error decode telegram response: %w", err)
	}

	log.Printf("TELEGRAM RESPONSE: %#v\n", data)
	return nil
}

func TelegramNotification(message string) error {
	if message == "" {
		message = "*"
	}
	return TelegramCommand("sendMessage", map[string]interface{}{
		"chat_id": os.Getenv("TELEGRAM_OPERATOR_ID"),
		"text":    message,
	})
}
