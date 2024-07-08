package main

import (
	"fmt"
	"log"
	"net/http"
	"time"
)

func streamHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	w.Header().Set("Transfer-Encoding", "chunked")
	w.Header().Set("X-Content-Type-Options", "nosniff")

	w.(http.Flusher).Flush()

	messages := []string{
		"This is the first chunk of text.",
		"Here's another piece of the stream.",
		"And the final message in this example.",
	}

	for _, msg := range messages {
		fmt.Fprintf(w, "%x\r\n%s\r\n", len(msg), msg)
		w.(http.Flusher).Flush()
		time.Sleep(1 * time.Second)
	}
	fmt.Fprint(w, "0\r\n\r\n")
}

func main() {
	http.HandleFunc("/", streamHandler)
	fmt.Println("listening on :8000...")
	log.Fatal(http.ListenAndServe(":8000", nil))
}
