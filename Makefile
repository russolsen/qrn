
PYTHON=pypy3
DST_DIR=dist

build: $(DST_DIR)
	$(PYTHON) -m build

$(DST_DIR):
	mkdir -f $@

install_local:
	 $(PYTHON) -m pip install .

clean:
	rm -rf $(DST_DIR)/*
