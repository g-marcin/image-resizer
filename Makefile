.PHONY: install dev venv run clean pm2-start pm2-stop pm2-restart pm2-logs pm2-status

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

pm2-start: install
ifeq ($(OS),Windows_NT)
	@echo "PM2 on Windows requires manual setup"
else
	chmod +x start.sh
	pm2 start ecosystem.config.js
endif

pm2-stop:
	pm2 stop image-resizer

pm2-restart:
	pm2 restart image-resizer

pm2-logs:
	pm2 logs image-resizer

pm2-status:
	pm2 status

pm2-delete:
	pm2 delete image-resizer


