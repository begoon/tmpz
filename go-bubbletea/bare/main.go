package main

import (
	"fmt"
	"log"
	"os"
	"strings"

	"go-bubbletea/bare/overlay"

	tea "github.com/charmbracelet/bubbletea"
	lipgloss "github.com/charmbracelet/lipgloss"
	"github.com/mattn/go-runewidth"
	"github.com/muesli/ansi"
)

type Main struct {
	index  int
	width  int
	height int
	overX  int
	overY  int
}

func (m Main) Init() tea.Cmd {
	return nil
}

func (m Main) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "enter":
			m.index = m.index + 1
		case "up":
			m.overY = max(m.overY-1, 0)
		case "down":
			m.overY = min(m.overY+1, m.height-5)
		case "left":
			m.overX = max(m.overX-1, 0)
		case "right":
			m.overX = min(m.overX+1, m.width-16)
		}
	}
	return m, cmd
}

func boxed(width, height int, title, content string) string {
	style := lipgloss.NewStyle().
		Bold(true).
		Width(width - 2).
		Height(height - 2).
		Border(lipgloss.RoundedBorder()).Align(lipgloss.Center).AlignVertical(lipgloss.Center)
	contentRender := style.Render(content)

	lines := strings.Split(contentRender, "\n")

	title = " " + title + " "
	titleRender := []rune(lipgloss.NewStyle().Background(lipgloss.Color("#00FF00")).Render(title))

	sb := strings.Builder{}

	titleY := len(lines) - 1
	r := []rune(lines[titleY])

	titleOffset := max((len(r) - len(title) - 2), 0)
	for i := range titleOffset {
		sb.WriteRune(r[i])
	}
	for i := range titleRender {
		sb.WriteRune(titleRender[i])
	}
	for i := titleOffset + len(title); i < len(r); i++ {
		sb.WriteRune(r[i])
	}
	lines[titleY] = sb.String()

	return strings.Join(lines, "\n")
}

func (m Main) View() string {
	if m.width == 0 {
		return "loading..."
	}
	content := fmt.Sprintf("width: %d, height: %d, index: %d", m.width, m.height, m.index)
	v := lipgloss.JoinHorizontal(
		lipgloss.Bottom,
		boxed(m.width/2, m.height-3, "title 1", content),
		boxed(m.width/2, m.height-3, "title 2", content),
	)
	msg := boxed(16, 5, "error", "overlay")

	v = overlay.PlaceOverlay(m.overX, m.overY, msg, v, true)

	lines := strings.Split(v, "\n")
	maxSz := 0
	lengths := []int{}
	for _, line := range lines {
		sz := runewidth.StringWidth(line)
		lengths = append(lengths, ansi.PrintableRuneWidth(line))
		if sz > maxSz {
			maxSz = sz
		}
	}

	v += "\n" + fmt.Sprintf("view: %d x %d %v", maxSz, len(lines), lengths)
	return v
}

func main() {
	main := &Main{}

	f, err := tea.LogToFile("debug.log", "debug")
	if err != nil {
		fmt.Println("fatal:", err)
		os.Exit(1)
	}
	defer f.Close()
	p := tea.NewProgram(*main, tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		log.Fatal(err)
	}
}
