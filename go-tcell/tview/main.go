package main

import (
	"log"

	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

func main() {
	app := tview.NewApplication()

	box := tview.NewBox()
	modal := tview.NewModal().
		SetText("Do you want to quit the application?").
		AddButtons([]string{"Quit", "Cancel"}).
		SetDoneFunc(func(buttonIndex int, buttonLabel string) {
			if buttonLabel == "Quit" {
				app.Stop()
			}
			if buttonLabel == "Cancel" {
				app.SetRoot(box, true)
			}
		}).SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
		switch event.Key() {
		case tcell.KeyEscape:
			app.SetRoot(box, true)
		}
		return event
	})

	box.SetBorder(true).SetTitle("| commanger |").
		SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
			switch event.Key() {
			case tcell.KeyCtrlC, tcell.KeyEscape:
				app.SetRoot(modal, false)
			}
			switch event.Rune() {
			case 'q':
				app.SetRoot(modal, true)
			}
			return event
		})
	if err := app.SetRoot(box, true).Run(); err != nil {
		log.Fatalf("start application: %v", err)
	}
}
