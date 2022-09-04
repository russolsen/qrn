
SITE_SCRIPT=site.py
#PYTHON=python
PYTHON=pypy3
DST_DIR=output
PORT=7717

#export PYTHONPATH=.:bin

build:
	$(PYTHON) $(SITE_SCRIPT)

serve:
	$(PYTHON) -m http.server --directory $(DST_DIR) $(PORT)

install-local:
	$(PYTHON) -m pip install -e .

clean-styles:
	rm -rf $(DST_DIR)/stylesheets

clean:
	rm -rf $(DST_DIR)/*
	rm -f site.log
