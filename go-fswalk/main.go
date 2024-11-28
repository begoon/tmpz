package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/charlievieth/fastwalk"

	"github.com/AlecAivazis/survey/v2"
	"github.com/AlecAivazis/survey/v2/terminal"
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
	err := fastwalk.Walk(nil, path, func(filePath string, dir fs.DirEntry, err error) error {
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

func walk(startFolder string, re *regexp.Regexp) (results []folderInfo, scanned int64) {
	lock := sync.Mutex{}
	results = make([]folderInfo, 0, 1024*256)

	scanned = 0
	err := fastwalk.Walk(nil, startFolder, func(path string, dir fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		if !dir.IsDir() {
			return nil
		}
		atomic.AddInt64(&scanned, 1)

		if !re.MatchString(dir.Name()) {
			return nil
		}

		if *verbose {
			fmt.Printf("processing %s\n", path)
		}

		size, err := directorySize(path)
		if err != nil {
			log.Fatalf("error calculating size of %s: %s\n", path, err)
		}

		lock.Lock()
		results = append(results, folderInfo{path, size})
		lock.Unlock()
		return filepath.SkipDir
	})
	if err != nil {
		log.Fatalf("error walking directory: %s\n", err)
	}
	sort.Slice(results, func(i, j int) bool {
		return (results)[i].size > (results)[j].size
	})
	return
}

func confirm(message string) bool {
	yes := false
	prompt := &survey.Confirm{Message: message}
	err := survey.AskOne(prompt, &yes)
	if err != nil {
		log.Fatalf("error asking question: %s", err)
	}
	return yes
}

func deleteFolder(path string) {
	if !confirm(fmt.Sprintf(`delete %q`, path)) {
		return
	}
	err := os.RemoveAll(path)
	if err != nil {
		log.Fatalf("error deleting folder: %s", err)
	}
	fmt.Println(c.Yellow(path).Bold(), c.BgRed("DELETED").Bold())
}

var (
	N       *int    = flag.Int("n", 10, "number of largest folders (0 for all)")
	delete  *bool   = flag.Bool("delete", false, "delete")
	command *string = flag.String("command", "du -hs {}", "command")
	script  *string = flag.String("script", "./fsclean.sh", "script name")
	verbose *bool   = flag.Bool("verbose", false, "verbose")
)

var CommonFolders = []string{".venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"}

type Settings struct {
	Folders []string `json:"folders"`
}

func (s *Settings) load() {
	data, err := os.ReadFile(settingsFile)
	if err == nil {
		json.Unmarshal(data, s)
	}
}

func (s Settings) store() error {
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(settingsFile, data, 0o644)
}

var (
	homeDir      string
	settingsFile string
)

func init() {
	var err error
	homeDir, err = os.UserHomeDir()
	if err != nil {
		fmt.Fprintf(os.Stderr, "error getting home directory: %s\n", err)
		os.Exit(1)
	}
	settingsFile = filepath.Join(homeDir, ".fsclean.json")
}

func main() {
	flag.Parse()

	settings := Settings{}
	settings.load()

	if *delete {
		fmt.Println(c.BrightYellow("delete"), c.BrightWhite("ENABLED").BgRed().Bold())
	}

	if len(flag.Args()) < 1 {
		fmt.Printf("usage: %s <start_folder> [<regex_pattern>]\n", os.Args[0])
		os.Exit(1)
	}
	startFolder := flag.Arg(0)

	regexPattern := flag.Arg(1)
	if regexPattern == "" {

		prompt := &survey.MultiSelect{
			Message: "where to search:",
			Options: CommonFolders,
			Default: settings.Folders,
		}
		folders := []string{}
		err := survey.AskOne(prompt, &folders, survey.WithValidator(survey.Required))
		if err != nil {
			if err == terminal.InterruptErr {
				os.Exit(0)
			}
			log.Fatalf("error asking question: %s", err)
		}
		settings.Folders = folders

		regexPattern = strings.Join(folders, "|")
		fmt.Printf("pattern: %s\n", regexPattern)
	}

	err := settings.store()
	if err != nil {
		log.Fatalf("error saving settings: %s", err)
	}

	if _, err := os.Stat(startFolder); os.IsNotExist(err) {
		log.Fatalf("error opening folder: %s", err)
	}

	re := regexp.MustCompile(regexPattern)

	started := time.Now()

	folderSizes, scanned := walk(startFolder, re)

	if *N > 0 && len(folderSizes) > *N {
		fmt.Printf(c.BrightWhite("%d largest folders\n").Underline().String(), *N)
		folderSizes = folderSizes[:*N]
	}

	total := int64(0)
	for _, result := range folderSizes {
		fmt.Printf("%s - %s\n", result.path, humanReadableSize(result.size))
		total += result.size
	}
	fmt.Printf("total size: %s / %d folder(s)\n", humanReadableSize(total), len(folderSizes))

	fmt.Printf("scanned: %d folder(s)\n", scanned)

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
			fmt.Printf("run it with: %s\n", c.Blue("source "+*script).Underline().String())
		}
		return
	}
}
