package main

import (
	"bytes"
	"os"
	"text/template"
)

func main() {
	t := template.New("main")
	t.Funcs(map[string]interface{}{
		"Render": func(name string, data interface{}) (string, error) {
			buf := bytes.NewBuffer([]byte{})
			err := t.ExecuteTemplate(buf, name, data)
			if err != nil {
				return "", err
			}
			return buf.String(), nil
		},
	})

	_, err := t.Parse(`Render "{{ .Callee }}" by name [{{Render .Callee .}}]`)
	if err != nil {
		panic(err)
	}

	_, err = t.New("callee").Parse(`subtemplate: {{ .Callee }}`)
	if err != nil {
		panic(err)
	}

	err = t.ExecuteTemplate(os.Stdout, "main", struct{ Callee string }{Callee: "callee"})
	if err != nil {
		panic(err)
	}
}
