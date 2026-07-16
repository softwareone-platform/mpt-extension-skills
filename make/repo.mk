## Add repo-specific targets here. Do not modify the shared *.mk files.

SHELLCHECK ?= shellcheck
runtime ?=
version ?=

check:  ## Run shellcheck validation
	$(SHELLCHECK) scripts/mpt-extensions-skills.sh scripts/mpt-extensions-skills-install.sh

test:  ## Run shell tests
	bash tests/test_mpt_skills.sh

test-scripts:  ## Run the pytest branch-coverage suite in Docker via docker compose (fails under 95%)
	docker compose run --build --rm tests

token-budget:  ## Report the token footprint of skill descriptions and bodies. Pass args="--check" to fail on over-limit descriptions
	python3 scripts/skill_token_budget.py $(args)

token-budget-check:  ## Fail if any skill description exceeds the token budget
	python3 scripts/skill_token_budget.py --check

check-links:  ## Fail if any internal (relative) Markdown link is broken (lychee via docker compose)
	docker compose run --rm links

check-all: check test test-scripts token-budget-check check-links  ## Run all validation and tests

install-skills:  ## Install skills from this local checkout. Pass runtime="--codex|--claude|--all" to target a runtime
	./scripts/mpt-extensions-skills.sh install --path "$(CURDIR)" $(runtime)

update-skills:  ## Upgrade installed skills from GitHub Releases. Pass version=<version> or runtime="--codex|--claude|--all"
	@command -v mpt-extensions-skills >/dev/null 2>&1 || { echo "Error: mpt-extensions-skills CLI not found. Run 'make install-skills' first."; exit 1; }
	mpt-extensions-skills upgrade $(if $(version),--version $(version)) $(runtime)
