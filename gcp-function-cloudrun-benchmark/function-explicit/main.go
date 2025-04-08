package greeting

import (
	"fmt"
	"net/http"

	"github.com/GoogleCloudPlatform/functions-framework-go/functions"
)

func init() {
	functions.HTTP("abc-function-explicit", greeting)
}

func greeting(w http.ResponseWriter, r *http.Request) {
	name := r.URL.Query().Get("name")
	if name == "" {
		name = "?"
	}
	fmt.Fprintf(w, "aloha %s!", name)
}
