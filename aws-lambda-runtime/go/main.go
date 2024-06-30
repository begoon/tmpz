package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

var DefaultHTTPGetAddress = "https://checkip.amazonaws.com"

type response struct {
	events.APIGatewayV2HTTPRequest
	Data struct {
		Status   string   `json:"status"`
		CallerIP string   `json:"callerIP"`
		When     string   `json:"when"`
		Env      []string `json:"env"`
	} `json:"data"`
}

func handler(request events.APIGatewayV2HTTPRequest) (events.APIGatewayProxyResponse, error) {
	slog.Info("[REQUEST]", "request", request)

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

	env := []string{}
	if request.QueryStringParameters["env"] != "" {
		env = os.Environ()
	}

	r := response{request, struct {
		Status   string   `json:"status"`
		CallerIP string   `json:"callerIP"`
		When     string   `json:"when"`
		Env      []string `json:"env"`
	}{
		Status:   "OK",
		CallerIP: string(ip),
		When:     time.Now().String(),
		Env:      env,
	}}

	serialized, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return events.APIGatewayProxyResponse{
			Body:       fmt.Sprintf("failed to marshal request: %v", err),
			StatusCode: 418,
		}, err
	}

	slog.Info("EVENT", "request", request)

	return events.APIGatewayProxyResponse{
		Body:       string(serialized),
		StatusCode: 200,
	}, nil
}

func main() {
	if os.Getenv("LAMBDA_TASK_ROOT") != "" {
		h := slog.NewJSONHandler(os.Stderr, &slog.HandlerOptions{
			Level: slog.LevelDebug,
			ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
				if a.Key == slog.LevelKey {
					a.Key = "severity"
					return a
				}
				if a.Key == slog.MessageKey {
					a.Key = "message"
					return a
				}
				return a
			},
		})
		slog.SetDefault(slog.New(h))
	}
	lambda.Start(handler)
}
