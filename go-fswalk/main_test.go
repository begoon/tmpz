package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"regexp"
	"testing"
)

func TestDirectorySize(t *testing.T) {
	root := t.TempDir()
	const directories, files, bytes = 40, 20, 100
	for i := range directories {
		dir := filepath.Join(root, fmt.Sprint(i))
		if err := os.Mkdir(dir, 0o700); err != nil {
			t.Fatal(err)
		}
		for j := range files {
			if err := os.WriteFile(filepath.Join(dir, fmt.Sprint(j)), make([]byte, bytes), 0o600); err != nil {
				t.Fatal(err)
			}
		}
	}
	sz, err := directorySize(root)
	if err != nil {
		t.Fatal(err)
	}
	if want := int64(directories * files * bytes); sz != want {
		t.Fatalf("directorySize = %d, want %d", sz, want)
	}
}

func TestPresetMatching(t *testing.T) {
	root := t.TempDir()
	for _, name := range []string{".venv", "target", "myXvenv-backup", "target-important", "Xvenv"} {
		if err := os.Mkdir(filepath.Join(root, name), 0o700); err != nil {
			t.Fatal(err)
		}
	}
	results, _ := walk(root, regexp.MustCompile(folderPattern([]string{".venv", "target"})))
	if len(results) != 2 {
		t.Fatalf("matched %d folders, want 2: %v", len(results), results)
	}
	for _, result := range results {
		name := filepath.Base(result.path)
		if name != ".venv" && name != "target" {
			t.Errorf("unexpected match: %s", name)
		}
	}
}

func TestShellCommand(t *testing.T) {
	for _, path := range []string{
		"/tmp/plain", "/tmp/with spaces", "/tmp/it's quoted", "/tmp/\"double\"",
		"/tmp/$(printf injected)", "/tmp/`printf injected`", "/tmp/a; printf injected",
		"/tmp/line\nbreak", "/tmp/*?[abc]", "/tmp/{}",
	} {
		t.Run(path, func(t *testing.T) {
			command := shellCommand("printf '%s\\n' {} {}", path)
			output, err := exec.Command("sh", "-c", command).CombinedOutput()
			if err != nil {
				t.Fatalf("shell command failed: %v: %s", err, output)
			}
			if want := path + "\n" + path + "\n"; string(output) != want {
				t.Fatalf("output = %q, want %q", output, want)
			}
		})
	}
}

func BenchmarkWalk(b *testing.B) {
	b.StopTimer()
	home := os.Getenv("HOME")
	folder := os.Getenv("FOLDER")
	if folder == "" {
		folder = "github"
	}
	startFolder := home + "/" + folder
	re := regexp.MustCompile("venv")
	b.StartTimer()
	for range b.N {
		walk(startFolder, re)
	}
}

func TestScriptFlag(t *testing.T) {
	for _, tc := range []struct {
		name string
		args []string
		want string
	}{
		{"omitted", nil, ""},
		{"bare", []string{"-script"}, "fsclean.sh"},
		{"explicit", []string{"-script=custom.sh"}, "custom.sh"},
		{"empty", []string{"-script="}, ""},
	} {
		t.Run(tc.name, func(t *testing.T) {
			fs := flag.NewFlagSet("fsclean", flag.ContinueOnError)
			var script scriptFlag
			fs.Var(&script, "script", "script output")
			positionals := []string{"/tmp/folders", "node_modules"}
			if err := fs.Parse(append(tc.args, positionals...)); err != nil {
				t.Fatal(err)
			}
			if string(script) != tc.want {
				t.Fatalf("script = %q, want %q", script, tc.want)
			}
			if !reflect.DeepEqual(fs.Args(), positionals) {
				t.Fatalf("positional arguments = %q, want %q", fs.Args(), positionals)
			}
		})
	}
}
