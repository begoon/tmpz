package main

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/coder/websocket"
	"github.com/go-resty/resty/v2"
)

type tracer struct {
	data     strings.Builder
	Monitors sync.Map
}

func (w *tracer) Write(p []byte) (n int, err error) {
	m := sync.Mutex{}
	m.Lock()
	defer m.Unlock()

	w.data.Write(p)
	w.Monitors.Range(func(_, v any) bool {
		ch := v.(chan string)
		ch <- strings.TrimSpace(string(p))
		return true
	})
	return len(p), nil
}

func (w *tracer) String() string {
	m := sync.Mutex{}
	m.Lock()
	defer m.Unlock()

	return w.data.String()
}

type Logger struct {
	l *log.Logger
}

func (l Logger) Errorf(format string, v ...interface{}) {
	l.l.Printf(format, v...)
}

func (l Logger) Debugf(format string, v ...interface{}) {
	l.l.Printf(format, v...)
}

func (l Logger) Warnf(format string, v ...interface{}) {
	l.l.Printf(format, v...)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}
	tracer := tracer{Monitors: sync.Map{}}

	http.HandleFunc("GET /", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		data := strings.Split(tracer.String(), "\n")
		for i := len(data) - 1; i >= 0; i-- {
			fmt.Fprintln(w, data[i])
		}
	})

	http.HandleFunc("GET /ws/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")

		tw := io.MultiWriter(os.Stdout, &tracer)
		l := log.New(tw, id+" | ", log.LstdFlags|log.Lmsgprefix)

		c, err := websocket.Accept(w, r, nil)
		if err != nil {
			msg := fmt.Sprintf("websocket handshake: %v", err)
			http.Error(w, msg, http.StatusBadRequest)
		}
		defer c.CloseNow()

		ctx, cancel := context.WithTimeout(context.Background(), time.Second*600)
		defer cancel()

		l.Printf("connected")

		var cerr error
		for {
			t, b, err := c.Read(ctx)
			if err != nil {
				var ce websocket.CloseError
				if errors.As(err, &ce) {
					l.Printf("read: %d %v", ce.Code, ce.Reason)
				} else {
					l.Printf("read: %v", err)
				}
				cerr = err
				break
			}
			var text string
			if t == websocket.MessageText {
				text = string(b)
			} else {
				text = fmt.Sprintf("%v", b)
			}
			l.Printf("received %s (%d): %v", t, len(b), text)
			if t == websocket.MessageText && len(b) > 0 && b[0] == '.' {
				reason := strings.TrimSpace(string(b[1:]))
				cerr = c.Close(websocket.StatusNormalClosure, reason)
				break
			}
			if t == websocket.MessageText {
				err = c.Write(ctx, websocket.MessageText, b)
			} else {
				err = c.Write(ctx, websocket.MessageBinary, b)
			}
			if err != nil {
				log.Printf("write: %v", err)
				cerr = err
				break
			}
		}
		code := 1000
		status := websocket.CloseStatus(cerr)
		if status != -1 {
			code = int(status)
		}
		l.Println("disconnected", code)
	})

	http.HandleFunc("GET /monitor", func(w http.ResponseWriter, r *http.Request) {
		c, err := websocket.Accept(w, r, nil)
		if err != nil {
			msg := fmt.Sprintf("websocket handshake: %v", err)
			http.Error(w, msg, http.StatusBadRequest)
			return
		}
		defer c.CloseNow()

		ch := make(chan string)
		id := time.Now().Format(time.RFC3339)
		tracer.Monitors.Store(id, ch)
		defer tracer.Monitors.Delete(id)

		ctx := r.Context()
		log.Printf("monitor/connected")
		go func() {
			for {
				if _, _, err := c.Read(ctx); err != nil {
					close(ch)
					return
				}
			}
		}()

		tmpl := `<div id="monitor" hx-swap-oob="afterbegin"><pre>{{.}}</pre></div>`
		t := template.Must(template.New("monitor").Parse(tmpl))
		for m := range ch {
			data := bytes.NewBuffer(nil)
			err := t.Execute(data, m)
			if err != nil {
				log.Printf("monitor/template: %v", err)
				return
			}
			err = c.Write(ctx, websocket.MessageText, data.Bytes())
			if err != nil {
				log.Printf("monitor/write: %v", err)
				return
			}
		}
		log.Printf("monitor/disconnected")
	})

	http.HandleFunc("GET /live", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprint(w, monitorHTML)
	})

	http.HandleFunc("GET /ip", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")

		tw := io.MultiWriter(os.Stdout, &tracer)
		l := log.New(tw, "ip | ", log.LstdFlags|log.Lmsgprefix)

		req := resty.New().R().
			SetContext(r.Context()).
			SetDebug(true).SetLogger(Logger{l})
		resp, err := req.Get("https://api.ipify.org")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		fmt.Fprintln(w, resp.String())
	})

	tw := io.MultiWriter(&tracer, os.Stdout)
	l := log.New(tw, "", log.LstdFlags|log.Lmsgprefix)

	l.Printf("listening on %s", port)
	l.Fatal(http.ListenAndServe(":"+port, nil))
}

const monitorHTML = `<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <script src="https://unpkg.com/htmx-ext-ws@2.0.2"></script>
	<meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
</head>
<div hx-ext="ws" ws-connect="/monitor"></div>
<div id="monitor" class="text-[0.7em]"></div>
<button hx-get="/ip" class="fixed right-0 top-0 p-2 bg-blue-500 text-white rounded">
  IP
</button>
</body>
</html>
`
