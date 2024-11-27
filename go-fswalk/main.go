package main

import (
	"flag"
	"fmt"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"runtime/debug"
	"sort"
	"strings"
	"time"

	"github.com/AlecAivazis/survey/v2"
	"github.com/logrusorgru/aurora/v4"
	c "github.com/logrusorgru/aurora/v4"
)

type colorFunc func(arg interface{}) c.Value

func hightlight(text string, colorizer colorFunc) string {
	return colorizer(text).Bold().String()
}

func humanReadableSize(bytes int64) string {
	const KB = 1024
	const MB = KB * 1024
	const GB = MB * 1024

	switch {
	case bytes >= GB:
		return hightlight(fmt.Sprintf("%.2f GB", float64(bytes)/float64(GB)), c.BrightRed)
	case bytes >= MB:
		return hightlight(fmt.Sprintf("%.2f MB", float64(bytes)/float64(MB)), c.BrightCyan)
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

func walk(startFolder string, re *regexp.Regexp, results *[]folderInfo, scanned *int, skipDirs map[string]bool) {
	err := filepath.WalkDir(startFolder, func(path string, dir fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		if dir.IsDir() {
			*scanned += 1
			if re.MatchString(dir.Name()) {
				skipDirs[path] = true
				fmt.Printf("processing %s\n", path)
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

func yesno(message string) bool {
	yesno := false
	prompt := &survey.Confirm{Message: message}
	err := survey.AskOne(prompt, &yesno)
	if err != nil {
		log.Fatalf("error asking question: %s", err)
	}
	return yesno
}

func deleteFolder(path string) {
	if !yesno(fmt.Sprintf(`delete %q`, path)) {
		return
	}

	err := os.RemoveAll(path)
	if err != nil {
		log.Fatalf("error deleting folder: %s", err)
	}
	fmt.Println(c.Yellow(path).Bold(), c.BgRed("DELETED").Bold())
}

var (
	delete  *bool   = flag.Bool("delete", false, "delete")
	command *string = flag.String("command", "du -hs {}", "command")
	script  *string = flag.String("script", "./fswalk.sh", "script name")
	verbose *bool   = flag.Bool("verbose", false, "verbose")
)

func main() {
	debug.SetGCPercent(-1)

	flag.Parse()

	if *delete {
		fmt.Println(c.BrightYellow("delete"), c.BrightWhite("ENABLED").BgRed().Bold())
	}

	if len(flag.Args()) != 2 {
		fmt.Printf("usage: %s <start_folder> <regex_pattern>\n", os.Args[0])
		os.Exit(1)
	}
	startFolder := flag.Arg(0)
	regexPattern := flag.Arg(1)

	if _, err := os.Stat(startFolder); os.IsNotExist(err) {
		log.Fatalf("error opening folder: %s", err)
	}

	folderSizes := make([]folderInfo, 0)
	scanned := 0

	skipDirs := make(map[string]bool)

	re := regexp.MustCompile(regexPattern)

	started := time.Now()

	walk(startFolder, re, &folderSizes, &scanned, skipDirs)

	sort.Slice(folderSizes, func(i, j int) bool {
		return folderSizes[i].size > folderSizes[j].size
	})

	total := int64(0)
	for _, result := range folderSizes {
		fmt.Printf("%s - %s\n", result.path, humanReadableSize(result.size))
		total += result.size
	}
	fmt.Printf("total size: %s / %d files\n", humanReadableSize(total), len(folderSizes))

	fmt.Printf("scanned: %d files\n", scanned)

	seconds := time.Since(started).Seconds()
	fmt.Printf("elapsed time: %.2f seconds\n", seconds)

	if *delete {
		for _, result := range folderSizes {
			fmt.Printf("%s - %s\n", result.path, humanReadableSize(result.size))
			deleteFolder(result.path)
		}
		return
	}

	if *command != "" {
		scriptFile := os.Stdout
		if *script != "" {
			var err error
			scriptFile, err = os.Create(*script)
			if err != nil {
				log.Fatalf("error creating script file: %s", err)
			}
			defer scriptFile.Close()
		}
		if len(folderSizes) > 0 {
			aurora.DefaultColorizer = aurora.New(aurora.WithColors(false))
			for _, result := range folderSizes {
				cmd := strings.ReplaceAll(*command, "{}", result.path)
				line := fmt.Sprintf("%s # %s", cmd, humanReadableSize(result.size))
				fmt.Fprintln(scriptFile, line)
				if *verbose {
					fmt.Println(line)
				}
			}
			aurora.DefaultColorizer = aurora.New(aurora.WithColors(true))
			fmt.Printf("script written to %v\n", *script)
			fmt.Printf("run it with: %s\n", c.BrightBlue("source "+*script).String())
		}
		return
	}
}
