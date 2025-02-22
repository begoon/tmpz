package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/coder/websocket"
)

var trace strings.Builder

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}
	http.HandleFunc("GET /", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		lines := strings.Split(trace.String(), "\n")
		for i := len(lines) - 1; i >= 0; i-- {
			fmt.Fprintln(w, lines[i])
		}
	})
	http.HandleFunc("GET /ws/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")

		tw := io.MultiWriter(&trace, os.Stdout)
		l := log.New(tw, id+" | ", log.LstdFlags|log.Lmsgprefix)

		c, err := websocket.Accept(w, r, nil)
		if err != nil {
			msg := fmt.Sprintf("websocket handshake: %v", err)
			http.Error(w, msg, http.StatusBadRequest)
		}
		defer c.CloseNow()

		ctx, cancel := context.WithTimeout(context.Background(), time.Second*30)
		defer cancel()

		l.Printf("connected")

		var cerr error
		for {
			t, b, err := c.Read(ctx)
			if err != nil {
				l.Printf("read: %v", err)
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
			if t == websocket.MessageText && b[0] == '.' {
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

	tw := io.MultiWriter(&trace, os.Stdout)
	l := log.New(tw, "", log.LstdFlags|log.Lmsgprefix)

	l.Printf("listening on %s", port)
	l.Fatal(http.ListenAndServe(":"+port, nil))
}
