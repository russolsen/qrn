SITE_SCRIPT=static.py
PYTHON=pypy3
DST_DIR=build
PORT=7720

.PHONY: release
release: clean build

r: release

.PHONY: build
build:
	$(PYTHON) static.py

.PHONY: serve
serve:
	$(PYTHON) -m http.server --directory $(DST_DIR) $(PORT)

s: serve

.PHONY: clean
clean:
	rm -rf $(DST_DIR)/*
	rm -f static.log
