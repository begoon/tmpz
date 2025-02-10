package main

import (
	_ "embed"
	"fmt"
	"os"
	"strings"
)

func main() {
	Completion()
}

var CompletionRoot = Args(
	NewArg("serve", "start server"),
	NewArg("listen", "listen on port"),
	NewArg("webhook", "manage webhook"),
	NewArg("configuration", "manage configuration"),
	NewArg("completion", "print completion script"),
	NewArg("--verbose", "verbose"),
	NewArg("--stub", "stub name"),
)

type Arg struct {
	Name, Descr string
}

func NewArg(name, descr string) Arg {
	return Arg{Name: name, Descr: descr}
}

func (a Arg) String() string {
	return fmt.Sprintf(`"%s":"%s"`, a.Name, a.Descr)
}

func Args(args ...Arg) string {
	v := make([]string, len(args))
	for _, a := range args {
		v = append(v, a.String())
	}
	return fmt.Sprintf(`_arguments '*: :((%s))'`, strings.Join(v, " "))
}

func Completion() {
	if os.Getenv("_EXE_COMPLETE") != "complete_zsh" {
		return
	}

	t := CompletionRoot
	args := os.Getenv("_EXE_COMPLETE_ARGS")

	if strings.HasPrefix(args, "local ") {
		t = Args()
	}
	if strings.HasPrefix(args, "serve ") {
		t = Args()
	}
	if strings.HasPrefix(args, "listen ") {
		t = Args(NewArg("-p", "port"), NewArg("-a", "address"))
	}
	if strings.HasPrefix(args, "webhook ") {
		t = Args(NewArg("--host", "set webhook"))
	}
	if strings.HasPrefix(args, "configuration ") {
		t = Args(NewArg("--encrypt", "encrypt"), NewArg("--decrypt", "decrypt"))
	}
	if strings.HasPrefix(args, "--stub ") {
		t = Args(NewArg("a", "type A"), NewArg("b", "type B"))
	}
	fmt.Printf("%s", t)
	os.Exit(0)
}

const completionsScript = `
#compdef exe

_exe() {
  eval $(env _EXE_COMPLETE_ARGS="${words[2,$CURRENT]}" _EXE_COMPLETE=complete_zsh exe)
}

compdef _exe exe
`

func CompletionScript() {
	fmt.Print(completionsScript)
}
