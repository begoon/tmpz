package gomoku

import "fmt"

func PrintBoard(g *Game) {
	for r := range N {
		for c := range N {
			var ch string
			switch g.at(Move{r, c}) {
			case Computer:
				ch = "O"
			case Human:
				ch = "X"
			default:
				ch = "."
			}
			fmt.Print(ch, " ")
		}
		fmt.Println()
	}
	fmt.Println()
}
