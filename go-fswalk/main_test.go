package main

import (
	"os"
	"regexp"
	"testing"
)

func BenchmarkWalk(b *testing.B) {
	b.StopTimer()
	home := os.Getenv("HOME")
	folder := os.Getenv("FOLDER")
	if folder == "" {
		folder = "github"
	}
	startFolder := home + "/" + folder
	re := regexp.MustCompile("venv")
	folderSizes := make([]folderInfo, 0)
	scanned := 0
	skipDirs := make(map[string]bool)
	b.StartTimer()
	for i := 0; i < b.N; i++ {
		walk(startFolder, re, &folderSizes, &scanned, skipDirs)
	}
}