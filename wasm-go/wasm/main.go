package main

import (
	"log/slog"
	"syscall/js"
)

type Request struct {
	Field []string
}

type Response struct {
	Value int
}

// JS-exposed function: window.processRequest({ Field: [...] }) -> { Value: ... }
func processRequest(this js.Value, args []js.Value) any {
	slog.Info("request", "args", args, "this", this)
	if len(args) < 1 {
		return map[string]any{"error": "missing argument 0 (Request)"}
	}

	arg0 := args[0]
	field := arg0.Get("Field")
	if field.IsUndefined() || field.IsNull() {
		return map[string]any{"error": "Request.Field is required"}
	}

	if field.Length() == 0 {
		// Empty array is fine; we'll just compute Value = 0
	}

	// Convert the JS array into []string
	n := field.Length()
	fields := make([]string, n)
	for i := 0; i < n; i++ {
		fields[i] = field.Index(i).String()
	}

	request := Request{Field: fields}

	// Your business logic: here we just count items
	response := Response{Value: len(request.Field)}

	// Returning a Go map[string]any (or struct via map) becomes a JS object
	return map[string]any{"Value": response.Value}
}

func main() {
	// Expose the function on the global object
	js.Global().Set("processRequest", js.FuncOf(processRequest))

	// Keep the Go program running
	select {}
}
