package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

var DefaultHTTPGetAddress = "https://checkip.amazonaws.com"

func handler(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
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

	request.Headers["INJECTED_HEADER"] = string(ip)

	data, err := json.MarshalIndent(request, "", "  ")
	if err != nil {
		return events.APIGatewayProxyResponse{
			Body:       fmt.Sprintf("failed to marshal request: %v", err),
			StatusCode: 418,
		}, err
	}

	// body := fmt.Sprintf(
	// 	"%s\ncalled from -> %v\n",
	// 	string(data), string(ip),
	// )

	body := fmt.Sprintf(
		"%s",
		string(data),
	)

	return events.APIGatewayProxyResponse{
		Body:       body,
		StatusCode: 200,
	}, nil
}

func main() {
	lambda.Start(handler)
}
