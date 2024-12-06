package main

import (
	"io"
	"log"
	"net/http"
)

const (
	metaURL = "http://metadata/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip"
)

func main() {
	client := &http.Client{}
	req, err := http.NewRequest("GET", metaURL, nil)
	if err != nil {
		log.Fatalf("error creating request: %v", err)
	}
	req.Header.Add("Metadata-Flavor", "Google")
	resp, err := client.Do(req)
	if err != nil {
		log.Fatalf("error getting external IP: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		log.Fatalf("error getting external IP: %v", resp.Status)
	}
	ip, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatalf("error reading response: %v", err)
	}
	println(string(ip))
}
