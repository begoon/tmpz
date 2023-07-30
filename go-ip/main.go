package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
)

func boom(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
func main() {
	r, err := http.Get("https://api.ipify.org")
	boom(err)
	defer r.Body.Close()
	ip, err := io.ReadAll(r.Body)
	boom(err)
	fmt.Println(string(ip))
}
