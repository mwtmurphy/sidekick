VENV_DIR ?= venv
PYTHON = $(VENV_DIR)/bin/python

pyenv: requirements.txt
	pip3 install virtualenv
	test -d venv || python3 -m virtualenv venv
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

tests:
	test -d venv || make pyenv
	${PYTHON} tests/test_admin_forms.py
	${PYTHON} tests/test_movements.py
	${PYTHON} tests/test_setup.py
	${PYTHON} tests/test_views.py

win-pyenv:
	pip3 install virtualenv
	python3 -m virtualenv venv
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt