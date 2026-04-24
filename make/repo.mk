## Add repo-specific targets here. Do not modify the shared *.mk files.

SHELLCHECK ?= shellcheck

check:  ## Run shellcheck validation
	$(SHELLCHECK) scripts/mpt-extensions-skills.sh scripts/mpt-extensions-skills-install.sh

test:  ## Run shell tests
	bash tests/test_mpt_skills.sh

check-all: check test  ## Run all validation and tests
