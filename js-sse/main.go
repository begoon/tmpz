package main

import (
	_ "embed"
	"log"
	"net/http"
	"time"

	"github.com/r3labs/sse/v2"
)

//go:embed index-go.html
var index []byte

func main() {
	server := sse.New()
	server.CreateStream("messages")

	mux := http.NewServeMux()
	mux.HandleFunc("/sse", func(w http.ResponseWriter, r *http.Request) {
		go func() {
			<-r.Context().Done()
			log.Println("client disconnected")
		}()
		server.ServeHTTP(w, r)
	})
	mux.HandleFunc("/time", func(w http.ResponseWriter, r *http.Request) {
		log.Println("time")
		server.Publish("messages", &sse.Event{
			Data: []byte(time.Now().Format(time.RFC3339)),
		})
		go func() {
			<-time.After(1 * time.Second)
			server.Publish("messages", &sse.Event{
				Data: []byte(time.Now().Format(time.RFC3339)),
			})
		}()
	})
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write(index)
	})
	http.ListenAndServe(":8000", mux)
}
