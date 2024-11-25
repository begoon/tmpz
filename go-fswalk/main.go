package main

import (
	"fmt"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"sort"
)

func humanReadableSize(bytes int64) string {
	const KB = 1024
	const MB = KB * 1024
	const GB = MB * 1024

	switch {
	case bytes >= GB:
		return fmt.Sprintf("%.2f GB", float64(bytes)/float64(GB))
	case bytes >= MB:
		return fmt.Sprintf("%.2f MB", float64(bytes)/float64(MB))
	case bytes >= KB:
		return fmt.Sprintf("%.2f KB", float64(bytes)/float64(KB))
	default:
		return fmt.Sprintf("%d bytes", bytes)
	}
}

func directorySize(path string) (int64, error) {
	var size int64
	err := filepath.WalkDir(path, func(filePath string, dir fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !dir.IsDir() {
			info, err := dir.Info()
			if err != nil {
				return err
			}
			size += info.Size()
		}
		return nil
	})
	return size, err
}

type folderInfo struct {
	path string
	size int64
}

func walk(startFolder string, re *regexp.Regexp, results *[]folderInfo, skipDirs map[string]bool) {
	err := filepath.WalkDir(startFolder, func(path string, dir fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		if dir.IsDir() {
			if re.MatchString(dir.Name()) {
				skipDirs[path] = true
				fmt.Printf("processing directory: %s\n", path)
				size, err := directorySize(path)
				if err != nil {
					log.Fatalf("error calculating size of %s: %s\n", path, err)
				}
				*results = append(*results, folderInfo{path, size})
			}
		}
		if skipDirs[path] {
			return filepath.SkipDir
		}
		return nil
	})
	if err != nil {
		log.Fatalf("error walking directory: %s\n", err)
	}
}

func main() {
	if len(os.Args) != 3 {
		fmt.Printf("usage: %s <start_folder> <regex_pattern>\n", os.Args[0])
		os.Exit(1)
	}
	startFolder := os.Args[1]
	regexPattern := os.Args[2]

	if _, err := os.Stat(startFolder); os.IsNotExist(err) {
		log.Fatalf("error opening folder: %s", err)
	}

	folderSizes := make([]folderInfo, 0)

	skipDirs := make(map[string]bool)

	re := regexp.MustCompile(regexPattern)

	walk(startFolder, re, &folderSizes, skipDirs)

	sort.Slice(folderSizes, func(i, j int) bool {
		return folderSizes[i].size > folderSizes[j].size
	})

	total := int64(0)
	for _, result := range folderSizes {
		fmt.Printf("%s - %s\n", result.path, humanReadableSize(result.size))
		total += result.size
	}
	fmt.Printf("total size: %s / %d\n", humanReadableSize(total), len(folderSizes))
}
