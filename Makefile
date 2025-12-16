lint:
	pre-commit run --all-files

build:
	docker compose build

run-docker:
	docker compose up

run-local:
	python3 logi_ha_bridge/runner.py

run: run-local

listen:
	python3 tools/listen_for_logi_buttons.py
