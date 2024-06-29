package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

var DefaultHTTPGetAddress = "https://checkip.amazonaws.com"

type response struct {
	events.APIGatewayV2HTTPRequest
	Data struct {
		Status   string `json:"status"`
		CallerIP string `json:"callerIP"`
		When     string `json:"when"`
	} `json:"data"`
}

func handler(request events.APIGatewayV2HTTPRequest) (events.APIGatewayProxyResponse, error) {
	fmt.Printf("[REQUEST]: %#v\n", request)

	resp, err := http.Get(DefaultHTTPGetAddress)
	if err != nil {
		return events.APIGatewayProxyResponse{}, err
	}

	if resp.StatusCode != 200 {
		return events.APIGatewayProxyResponse{}, err
	}

	ip, err := io.ReadAll(resp.Body)
	if err != nil {
		return events.APIGatewayProxyResponse{}, err
	}

	if len(ip) == 0 {
		return events.APIGatewayProxyResponse{}, err
	}

	if request.Headers == nil {
		request.Headers = make(map[string]string)
	}

	request.Headers["INJECTED_HEADER"] = string(ip)

	r := response{request, struct {
		Status   string `json:"status"`
		CallerIP string `json:"callerIP"`
		When     string `json:"when"`
	}{
		Status:   "OK",
		CallerIP: string(ip),
		When:     time.Now().String(),
	}}

	serialized, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return events.APIGatewayProxyResponse{
			Body:       fmt.Sprintf("failed to marshal request: %v", err),
			StatusCode: 418,
		}, err
	}

	return events.APIGatewayProxyResponse{
		Body:       string(serialized),
		StatusCode: 200,
	}, nil
}

func main() {
	lambda.Start(handler)
}
