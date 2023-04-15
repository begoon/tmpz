package main

import (
	"html/template"
	"net/http"
	"os"
	"strings"

	"log"

	"github.com/gorilla/pat"
	"github.com/gorilla/sessions"
	"github.com/markbates/goth"
	"github.com/markbates/goth/gothic"
	"github.com/markbates/goth/providers/google"
)

func main() {
	key := "-session!key-" // Replace with your SESSION_SECRET or similar
	maxAge := 86400 * 30   // 30 days
	isProd := false        // Set to true when serving over https

	store := sessions.NewCookieStore([]byte(key))
	store.MaxAge(maxAge)
	store.Options.Path = "/"
	store.Options.HttpOnly = true // HttpOnly should always be enabled
	store.Options.Secure = isProd

	gothic.Store = store

	goth.UseProviders(
		google.New(
			os.Getenv("GOOGLE_AUTH_CLIENT_KEY"),
			os.Getenv("GOOGLE_AUTH_SECRET"),
			"http://localhost:8000/auth/google/callback",
			"email",
			"profile",
		),
	)

	p := pat.New()
	p.Get("/auth/{provider}/callback", func(res http.ResponseWriter, req *http.Request) {
		user, err := gothic.CompleteUserAuth(res, req)
		if err != nil {
			http.Redirect(res, req, "/", http.StatusTemporaryRedirect)
			return
		}
		if !strings.HasSuffix(user.Email, "@iproov.com") {
			http.Error(res, "Unauthorized", http.StatusUnauthorized)
			return
		}
		t, _ := template.ParseFiles("templates/success.html")
		t.Execute(res, user)
	})

	p.Get("/auth/logout", func(res http.ResponseWriter, req *http.Request) {
		err := gothic.Logout(res, req)
		if err != nil {
			log.Println("error", res, err)
			http.Error(res, "Internal Server Error", http.StatusInternalServerError)
			return
		}
	})

	p.Get("/auth/{provider}", func(res http.ResponseWriter, req *http.Request) {
		gothic.BeginAuthHandler(res, req)
	})

	p.Get("/", func(res http.ResponseWriter, req *http.Request) {
		t, _ := template.ParseFiles("templates/index.html")
		t.Execute(res, false)
	})
	log.Fatal(http.ListenAndServe(":8000", p))
}
