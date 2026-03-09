lint:
	pre-commit run --all-files

build:
	docker compose build

run-docker:
	docker compose up

run-local:
	python3 logi_pop_switches/logi_ha_bridge/runner.py

run: run-local

listen:
	python3 tools/listen_for_logi_buttons.py

bump-patch:
	@cd logi_pop_switches && \
	OLD=$$(grep '^version:' config.yaml | sed 's/version: *"//;s/"//'); \
	MAJOR=$$(echo $$OLD | cut -d. -f1); \
	MINOR=$$(echo $$OLD | cut -d. -f2); \
	PATCH=$$(echo $$OLD | cut -d. -f3); \
	NEW="$$MAJOR.$$MINOR.$$((PATCH + 1))"; \
	sed -i "s/^version: \"$$OLD\"/version: \"$$NEW\"/" config.yaml && \
	sed -i "s/^version = \"$$OLD\"/version = \"$$NEW\"/" pyproject.toml && \
	echo "Bumped version: $$OLD -> $$NEW"

bump-minor:
	@cd logi_pop_switches && \
	OLD=$$(grep '^version:' config.yaml | sed 's/version: *"//;s/"//'); \
	MAJOR=$$(echo $$OLD | cut -d. -f1); \
	MINOR=$$(echo $$OLD | cut -d. -f2); \
	NEW="$$MAJOR.$$((MINOR + 1)).0"; \
	sed -i "s/^version: \"$$OLD\"/version: \"$$NEW\"/" config.yaml && \
	sed -i "s/^version = \"$$OLD\"/version = \"$$NEW\"/" pyproject.toml && \
	echo "Bumped version: $$OLD -> $$NEW"

bump-major:
	@cd logi_pop_switches && \
	OLD=$$(grep '^version:' config.yaml | sed 's/version: *"//;s/"//'); \
	MAJOR=$$(echo $$OLD | cut -d. -f1); \
	NEW="$$((MAJOR + 1)).0.0"; \
	sed -i "s/^version: \"$$OLD\"/version: \"$$NEW\"/" config.yaml && \
	sed -i "s/^version = \"$$OLD\"/version = \"$$NEW\"/" pyproject.toml && \
	echo "Bumped version: $$OLD -> $$NEW"
