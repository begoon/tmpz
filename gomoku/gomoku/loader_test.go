package gomoku

import (
	"testing"
)

func createGame() (*Game, []string) {
	g := NewGame()

	g.Place(Move{0, 0}, Human)
	g.Place(Move{N - 1, N - 1}, Human)
	g.Place(Move{7, 7}, Human)
	g.Place(Move{8, 7}, Computer)
	g.Place(Move{8, 8}, Human)
	g.Place(Move{7, 8}, Computer)
	g.Place(Move{0, N - 1}, Computer)
	g.Place(Move{N - 1, 0}, Computer)

	field := []string{
		"X.............O",
		"...............",
		"...............",
		"...............",
		"...............",
		"...............",
		"...............",
		".......XO......",
		".......OX......",
		"...............",
		"...............",
		"...............",
		"...............",
		"...............",
		"O.............X",
	}
	return g, field
}

func TestExportImport(t *testing.T) {
	g, expected := createGame()

	exported := g.Export()

	for r := range N {
		if exported.Field[r] != expected[r] {
			t.Errorf("row %d: got %q, want %q", r, exported.Field[r], expected[r])
		}
	}

	imported := Import(&exported)
	for r := range N {
		for c := range N {
			m := Move{r, c}
			if imported.at(m) != g.at(m) {
				t.Errorf("at (%d,%d): imported %q, want %q", r, c, imported.at(m), g.at(m))
			}
		}
	}
}

func TestExportImportJSON(t *testing.T) {
	g, expected := createGame()

	exported := g.ExportJSON()
	imported := ImportJSON(exported)
	for r := range N {
		for c := range N {
			m := Move{r, c}
			if imported.at(m) != expected[r][c] {
				t.Errorf("at (%d,%d): imported %q, want %q", r, c, imported.at(m), expected[r][c])
			}
		}
	}
}
