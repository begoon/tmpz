package gomoku

import "encoding/json"

type GameExport struct {
	Field []string `json:"field"`
}

func (g *Game) Export() GameExport {
	field := make([]string, N)
	for r := range N {
		row := make([]byte, N)
		for c := range N {
			row[c] = g.at(Move{r, c})
		}
		field[r] = string(row)
	}
	return GameExport{Field: field}
}

func (g *Game) ExportJSON() string {
	v := g.Export()
	data, _ := json.MarshalIndent(v, "", "  ")
	return string(data)
}

func Import(v *GameExport) *Game {
	g := NewGame()
	for r := range N {
		for c := range N {
			m := Move{r, c}
			g.Place(m, v.Field[r][c])
		}
	}
	return g
}

func ImportJSON(data string) *Game {
	var v GameExport
	json.Unmarshal([]byte(data), &v)
	return Import(&v)
}
