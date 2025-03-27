package main

import (
	"fmt"
	"log"
	"strings"

	"github.com/gdamore/tcell/v2"
)

func drawText(s tcell.Screen, x1, y1, x2, y2 int, style tcell.Style, text string) {
	row := y1
	col := x1
	for _, r := range text {
		s.SetContent(col, row, r, nil, style)
		col++
		if col >= x2 {
			row++
			col = x1
		}
		if row > y2 {
			break
		}
	}
}

func drawBox(s tcell.Screen, x1, y1, x2, y2 int, style tcell.Style, text string) {
	if y2 < y1 {
		y1, y2 = y2, y1
	}
	if x2 < x1 {
		x1, x2 = x2, x1
	}

	// Fill background
	for row := y1; row <= y2; row++ {
		for col := x1; col <= x2; col++ {
			s.SetContent(col, row, ' ', nil, style)
		}
	}

	// Draw borders
	for col := x1; col <= x2; col++ {
		s.SetContent(col, y1, tcell.RuneHLine, nil, style)
		s.SetContent(col, y2, tcell.RuneHLine, nil, style)
	}
	for row := y1 + 1; row < y2; row++ {
		s.SetContent(x1, row, tcell.RuneVLine, nil, style)
		s.SetContent(x2, row, tcell.RuneVLine, nil, style)
	}

	// Only draw corners if necessary
	if y1 != y2 && x1 != x2 {
		s.SetContent(x1, y1, tcell.RuneULCorner, nil, style)
		s.SetContent(x2, y1, tcell.RuneURCorner, nil, style)
		s.SetContent(x1, y2, tcell.RuneLLCorner, nil, style)
		s.SetContent(x2, y2, tcell.RuneLRCorner, nil, style)
	}

	drawText(s, x1+1, y1+1, x2-1, y2-1, style, text)

	titleStyle := style.Foreground(tcell.ColorWhite).Background(tcell.ColorPurple).Reverse(true)
	drawText(s, x1+2, y1, x2, y1, titleStyle, " TITLE ")

	// draw shadow
	shadowStyle := style.Foreground(tcell.ColorBlack).Background(tcell.ColorBlack)
	for row := y1 + 1; row <= y2; row++ {
		s.SetContent(x2+1, row, ' ', nil, shadowStyle)
	}
	for col := x1 + 1; col <= x2+1; col++ {
		s.SetContent(col, y2+1, ' ', nil, shadowStyle)
	}
}

func drawButton(s tcell.Screen, x, y, w int, down bool, style tcell.Style, text string) {
	w = max(len(text)+2, w)
	sz := len(text)
	leftPad := (w - sz) / 2
	rightPad := w - sz - leftPad
	if !down {
		drawText(s, x, y, x+w, y, style, strings.Repeat(" ", leftPad)+text+strings.Repeat(" ", rightPad))
		shadowStyle := style.Foreground(tcell.ColorBlack).Background(tcell.ColorBlack)
		for row := y + 1; row <= y+1; row++ {
			s.SetContent(x+w, row, ' ', nil, shadowStyle)
		}
		for col := x + 1; col <= x+w; col++ {
			s.SetContent(col, y+1, ' ', nil, shadowStyle)
		}
	} else {
		drawText(s, x+1, y+1, x+w+1, y+1, style, strings.Repeat(" ", leftPad)+text+strings.Repeat(" ", rightPad))
	}
}

type tickEvent struct {
	tcell.Event
}

func main() {
	defStyle := tcell.StyleDefault.Background(tcell.ColorReset).Foreground(tcell.ColorReset)
	boxStyle := tcell.StyleDefault.Foreground(tcell.ColorWhite).Background(tcell.ColorPurple)

	buttonStyle := tcell.StyleDefault.Foreground(tcell.ColorWhite).Background(tcell.ColorYellow)

	s, err := tcell.NewScreen()
	if err != nil {
		log.Fatalf("%+v", err)
	}
	if err := s.Init(); err != nil {
		log.Fatalf("%+v", err)
	}
	s.SetStyle(defStyle)
	s.EnableMouse()
	s.EnablePaste()
	s.Clear()

	drawBox(s, 1, 1, 42, 7, boxStyle, "Click and drag to draw a box")

	drawButton(s, 3, 4, 16, false, buttonStyle, "Button")

	quit := func() {
		maybePanic := recover()
		s.Fini()
		if maybePanic != nil {
			panic(maybePanic)
		}
	}
	defer quit()

	xmax, ymax := s.Size()
	x, y := 0, 0
	for {
		s.Show()

		ev := s.PollEvent()

		keyName := ""

		switch ev := ev.(type) {
		case *tcell.EventResize:
			xmax, ymax := s.Size()
			size := fmt.Sprintf("%d x %d  ", xmax, ymax)
			drawText(s, xmax-len(size), ymax-1, xmax-1, ymax-1, defStyle, size)
		case *tcell.EventKey:
			keyName = ev.Name()
			if ev.Key() == tcell.KeyEscape || ev.Rune() == 'q' {
				return
			}
		case *tcell.EventMouse:
			x, y = ev.Position()
			down := false
			switch ev.Buttons() {
			case tcell.Button1, tcell.Button2:
				down = true
			case tcell.ButtonNone:
				down = false
			}

			drawBox(s, 1, 1, 42, 7, boxStyle, "Click and drag to draw a box")
			drawButton(s, 3, 4, 16, down, buttonStyle, "Button")
		}
		v := fmt.Sprintf("      %v %d x %d", keyName, x, y)
		drawText(s, xmax-len(v)-1, ymax-1, xmax-1, ymax-1, defStyle, v)
	}
}
