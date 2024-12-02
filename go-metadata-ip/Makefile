all: build check pack install

NAME := external-ip

build:
	CGO_ENABLED=0 go build -ldflags="-s -w" -o $(NAME) ./.

pack:
	upx -9 $(NAME)

install:
	@mv $(NAME) $(HOME)/.local/bin/

check:
	@ls -al $(NAME)
	@file $(NAME)
	-@(ldd $(NAME) 2>&1 | sed 's/\t//g')