.PHONY: test
test: venv
	$(VENV)/python -m unittest


.PHONY: test-verbose
test-verbose: venv
	$(VENV)/python -m unittest -v


.PHONY: test-interactive
test-interactive: venv
	$(VENV)/python tests/test_fetchers_interactive.py


include Makefile.venv
Makefile.venv:
	curl \
		-o Makefile.fetched \
		-L "https://github.com/sio/Makefile.venv/raw/v2019.10.04/Makefile.venv"
	echo "7a0a5a7a25ab959c6686b839cd45eb522f1a0662aa6096be5d56106c940aee95 *Makefile.fetched" \
		| sha256sum --check - \
		&& mv Makefile.fetched Makefile.venv
