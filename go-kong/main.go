package main

import (
	"fmt"
	"os"

	// "os"

	"github.com/alecthomas/kong"
	kongcompletion "github.com/jotaen/kong-completion"
)

type Context struct {
	Debug bool
}

type RmCmd struct {
	Force     bool `help:"Force removal."`
	Recursive bool `help:"Recursively remove files."`

	Paths []string `arg:"" name:"path" help:"Paths to remove." type:"path"`
}

func (r *RmCmd) Run(ctx *Context) error {
	fmt.Printf("CMD: rm %#v\n", r)
	return nil
}

type LsCmd struct {
	Tags  string   `arg:"" optional:"" name:"tags" help:"Tags to list." type:"string"`
	Paths []string `arg:"" optional:"" help:"Paths to list." type:"path"`
}

func (l *LsCmd) Run(ctx *Context) error {
	fmt.Println("CMD: ls")
	fmt.Printf("paths=%v script=%v tags=%v\n", l.Paths, cli.Script, l.Tags)
	return nil
}

var cli struct {
	Debug   bool `help:"enable debug mode or use DEBUG=1"`
	Verbose bool `flag:"" help:"enable verbose mode"`

	Rm RmCmd `cmd:"" help:"remove files"`
	Ls LsCmd `cmd:"" help:"list paths"`

	Script string `kong:"flag,short='s',default='fsclean.sh',type='string',help='script name to generate'"`

	Completion *kongcompletion.Completion `cmd:"" help:"outputs shell code for initialising tab completions"`
}

func main() {
	application := kong.Must(&cli)
	kongcompletion.Register(application)

	ctx := kong.Parse(&cli)

	err := ctx.Run(&Context{Debug: cli.Debug && os.Getenv("DEBUG") == "1"})
	ctx.FatalIfErrorf(err)
}
