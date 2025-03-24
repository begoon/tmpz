package main

import (
	"fmt"
	"log"
	"os"
	"slices"

	tea "github.com/charmbracelet/bubbletea"
	lipgloss "github.com/charmbracelet/lipgloss"
)

type Main struct {
	index  int
	width  int
	height int
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
			return m, nil
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
	contentRender := []rune(style.Render(content))
	title = " " + title + " "
	titleRender := []rune(lipgloss.NewStyle().Background(lipgloss.Color("#00FF00")).Render(title))
	contentRender = slices.Delete(contentRender, 2, 2+len(title))
	contentRender = slices.Insert(contentRender, 2, []rune(titleRender)...)
	return string(contentRender)
}

func (m Main) View() string {
	if m.width == 0 {
		return "loading..."
	}
	content := fmt.Sprintf("width: %d, height: %d, index: %d", m.width, m.height, m.index)
	return lipgloss.JoinHorizontal(
		lipgloss.Bottom,
		boxed(m.width/2, m.height, "title 1", content),
		boxed(m.width/2, m.height, "title 2", content),
	)
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
