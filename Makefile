.PHONY: install dev venv run clean

ifeq ($(OS),Windows_NT)
    PYTHON := python
    VENV_BIN := venv\Scripts
    PIP := $(VENV_BIN)\pip.exe
    UVICORN := $(VENV_BIN)\uvicorn.exe
    RM := rmdir /s /q
else
    PYTHON := python3
    VENV_BIN := venv/bin
    PIP := $(VENV_BIN)/pip
    UVICORN := $(VENV_BIN)/uvicorn
    RM := rm -rf
endif

venv:
	$(PYTHON) -m venv venv

install: venv
	$(PIP) install -r requirements.txt

dev: install
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8001 --reload

run: install
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8001

clean:
	$(RM) venv 2>nul || true


