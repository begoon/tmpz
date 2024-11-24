package main

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"sync"
	"time"
)

type Structure struct {
	UserAgent string `json:"user-agent"`
}

const HTTPBIN_API = "https://httpbin.org"

func fetch_delay(delay int) (int, error) {
	url := fmt.Sprintf("%s/delay/%d", HTTPBIN_API, delay)
	fmt.Printf("dialing %s\n", url)

	response, err := http.Get(url)
	return response.StatusCode, err
}

func fetch_structure() (Structure, error) {
	url := fmt.Sprintf("%s/user-agent", HTTPBIN_API)
	fmt.Printf("dialing %s\n", url)

	request, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return Structure{}, fmt.Errorf("error creating request: %w", err)
	}
	request.Header.Set("User-Agent", "teapot/1.0")

	client := http.Client{Timeout: 10 * time.Second}
	response, err := client.Do(request)
	if err != nil {
		return Structure{}, fmt.Errorf("error calling user-agent/: %w", err)
	}
	defer response.Body.Close()

	decoder := json.NewDecoder(response.Body)
	var data Structure
	return data, decoder.Decode(&data)
}

func fetch_json() (map[string]interface{}, error) {
	url := fmt.Sprintf("%s/json", HTTPBIN_API)
	fmt.Printf("dialing %s\n", url)

	response, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("error calling json/: %w", err)
	}
	defer response.Body.Close()

	decoder := json.NewDecoder(response.Body)
	var data map[string]interface{}
	return data, decoder.Decode(&data)
}

func main() {
	wg := sync.WaitGroup{}

	jobs := []func() (interface{}, error){
		func() (interface{}, error) {
			return fetch_structure()
		},
		func() (interface{}, error) {
			return fetch_json()
		},
	}

	for i := 0; i < 2; i++ {
		delay := rand.Intn(5) + 1
		job := func() (interface{}, error) {
			return fetch_delay(delay)
		}
		jobs = append(jobs, job)
	}

	for _, job := range jobs {
		wg.Add(1)
		go func(job func() (interface{}, error)) {
			defer wg.Done()
			data, err := job()
			if err != nil {
				fmt.Printf("error: %s\n", err)
				return
			}
			fmt.Printf("response: %v\n", data)
		}(job)
	}
	wg.Wait()
}
