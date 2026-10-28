package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"testing"
)

func TestDirectorySize(t *testing.T) {
	root := t.TempDir()
	const directories, files, bytes = 40, 20, 100
	for i := 0; i < directories; i++ {
		dir := filepath.Join(root, fmt.Sprint(i))
		if err := os.Mkdir(dir, 0o700); err != nil {
			t.Fatal(err)
		}
		for j := 0; j < files; j++ {
			if err := os.WriteFile(filepath.Join(dir, fmt.Sprint(j)), make([]byte, bytes), 0o600); err != nil {
				t.Fatal(err)
			}
		}
	}
	got, err := directorySize(root)
	if err != nil {
		t.Fatal(err)
	}
	if want := int64(directories * files * bytes); got != want {
		t.Fatalf("directorySize = %d, want %d", got, want)
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
	for i := 0; i < b.N; i++ {
		walk(startFolder, re)
	}
}
