.PHONY: setup
setup:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -r requirements-dev.txt
	venv/bin/pip install .

format:
	venv/bin/black \
	    --line-length 120 \
		stravaviz

lint:
	venv/bin/pylint \
	    stravaviz
	venv/bin/mypy \
	    stravaviz
	venv/bin/codespell  \
	    README.md stravaviz/*.py
	venv/bin/black \
	    --line-length 120 \
	    --check \
	    --diff \
	    stravaviz
