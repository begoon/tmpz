package function

import (
	"fmt"
	"net/http"
	"time"
)

func Handler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	fmt.Fprintf(w, "latency: %s\n", time.Since(start))
}
