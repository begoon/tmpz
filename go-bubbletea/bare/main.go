package main

import (
	"fmt"
	"log"
	"os"

	"go-bubbletea/bare/overlay"

	tea "github.com/charmbracelet/bubbletea"
	lipgloss "github.com/charmbracelet/lipgloss"
	"github.com/mattn/go-runewidth"
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

func boxed(width, height int, title, content, fgColor, bgColor string) string {
	style := lipgloss.NewStyle().
		Bold(true).
		Width(width - 2).
		Height(height - 2).
		Background(lipgloss.Color(bgColor)).
		Foreground(lipgloss.Color(fgColor)).
		Border(lipgloss.RoundedBorder()).
		BorderBackground(lipgloss.Color(bgColor)).
		BorderForeground(lipgloss.Color(fgColor)).
		Align(lipgloss.Center).AlignVertical(lipgloss.Center)
	contentRender := style.Render(content)

	title = " " + title + " "
	titleRender := lipgloss.NewStyle().Background(lipgloss.Color("#00FF00")).Render(title)

	titleX := (width - runewidth.StringWidth(title)) / 2
	return overlay.PlaceOverlay(titleX, 0, titleRender, contentRender, "", false)
}

func (m Main) View() string {
	if m.width == 0 {
		return "loading..."
	}
	content := fmt.Sprintf("width: %d, height: %d, index: %d", m.width, m.height, m.index)
	v := lipgloss.JoinHorizontal(
		lipgloss.Bottom,
		boxed(m.width/2, m.height-3, "title 1", content, "#00FF00", "#000000"),
		boxed(m.width/2, m.height-3, "title 2", content, "#0000FF", "#FFFFFF"),
	)
	msg := boxed(16, 5, "error", "overlay", "#FFFFFF", "#FF0000")

	v = overlay.PlaceOverlay(m.overX, m.overY, msg, v, "#000000", true)
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
