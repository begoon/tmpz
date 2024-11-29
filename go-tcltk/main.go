package main

import tk "modernc.org/tk9.0"

func main() {
	tk.Pack(
		tk.TButton(tk.Txt("Hello"), tk.Command(func() { tk.Destroy(tk.App) })),
		tk.Ipadx(10), tk.Ipady(5), tk.Padx(20), tk.Pady(10),
	)
	tk.App.Wait()
}
