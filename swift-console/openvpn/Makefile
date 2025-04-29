.PHONY: build release

all: run

FILES = accounts.swift base32.swift totp.swift controller.swift

release: clean build
	-rm -rf release
	mkdir release
	cp -r build/Release/OTP/VPN.app release
	
build:
	xcodebuild

clean:
	-rm -rf build

