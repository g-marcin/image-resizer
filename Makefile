.PHONY: install dev venv run clean

venv:
	python -m venv venv

install: venv
	.\venv\Scripts\pip.exe install -r requirements.txt

dev: install
	.\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8001 --reload

run: install
	.\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8001

clean:
	rmdir /s /q venv 2>nul || true


