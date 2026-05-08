## Add repo-specific targets here. Do not modify the shared *.mk files.

SHELLCHECK ?= shellcheck
runtime ?=
version ?=

check:  ## Run shellcheck validation
	$(SHELLCHECK) scripts/mpt-extensions-skills.sh scripts/mpt-extensions-skills-install.sh

test:  ## Run shell tests
	bash tests/test_mpt_skills.sh

check-all: check test  ## Run all validation and tests

install-skills:  ## Install skills from this local checkout. Pass runtime="--codex|--claude|--all" to target a runtime
	./scripts/mpt-extensions-skills.sh install --path "$(CURDIR)" $(runtime)

update-skills:  ## Upgrade installed skills from GitHub Releases. Pass version=<version> or runtime="--codex|--claude|--all"
	mpt-extensions-skills upgrade $(if $(version),--version $(version)) $(runtime)
