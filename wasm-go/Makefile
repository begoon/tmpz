WEB_DIR := web
WASM_DIR := wasm
WASM_OUT := $(WEB_DIR)/main.wasm
WASM_EXEC := $(WEB_DIR)/wasm_exec.js

.PHONY: all build serve clean

all: build

build:
	GOOS=js GOARCH=wasm go build -o $(WASM_OUT) ./$(WASM_DIR)
	@mkdir -p $(WEB_DIR)
	cp "$$(go env GOROOT)/lib/wasm/wasm_exec.js" $(WASM_EXEC)

serve:
	python3 -m http.server -d $(WEB_DIR) 8000 

clean:
	@rm -f $(WASM_OUT) $(WASM_EXEC)
