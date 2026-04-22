#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SCRIPT_PATH="${REPO_ROOT}/scripts/mpt-skills.sh"

TESTS_RUN=0

fail() {
  printf '[FAIL] %s\n' "$*" >&2
  exit 1
}

pass() {
  printf '[PASS] %s\n' "$*"
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  if [[ "${haystack}" != *"${needle}"* ]]; then
    fail "Expected output to contain: ${needle}"
  fi
}

assert_exists() {
  local path="$1"
  [[ -e "${path}" ]] || fail "Expected path to exist: ${path}"
}

assert_not_exists() {
  local path="$1"
  [[ ! -e "${path}" ]] || fail "Expected path to not exist: ${path}"
}

assert_symlink_target() {
  local path="$1"
  local expected="$2"
  [[ -L "${path}" ]] || fail "Expected symlink: ${path}"
  local actual
  actual="$(readlink "${path}")"
  [[ "${actual}" == "${expected}" ]] || fail "Expected ${path} -> ${expected}, got ${actual}"
}

run_with_env() {
  local tmp_root="$1"
  shift
  env \
    MPT_EXTENSION_SKILLS_HOME="${tmp_root}/store" \
    CODEX_SKILLS_DIR="${tmp_root}/codex/skills" \
    CLAUDE_SKILLS_DIR="${tmp_root}/claude/skills" \
    MPT_SKILLS_BIN_DIR="${tmp_root}/bin" \
    "${SCRIPT_PATH}" "$@"
}

test_help_without_install() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  local output
  output="$(run_with_env "${tmp_root}" --help)"

  assert_contains "${output}" 'Usage:'
  assert_contains "${output}" 'Environment overrides:'
  assert_contains "${output}" 'MPT_EXTENSION_SKILLS_HOME  Install root for versioned package contents'
  assert_contains "${output}" 'CODEX_SKILLS_DIR           Codex skills directory to wire during activation'
  assert_contains "${output}" 'CLAUDE_SKILLS_DIR          Claude skills directory to wire during activation'
  assert_contains "${output}" 'MPT_SKILLS_BIN_DIR         Directory where the user-facing mpt-skills command is linked'
  assert_contains "${output}" 'Current installed version:'
  assert_contains "${output}" 'not installed'
  pass "${FUNCNAME[0]}"
}

test_list_without_install() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  local output
  output="$(run_with_env "${tmp_root}" list)"

  assert_contains "${output}" 'No installed versions found'
  pass "${FUNCNAME[0]}"
}

test_list_marks_active_version() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex"
  run_with_env "${tmp_root}" install 1.0.0 --codex >/dev/null
  run_with_env "${tmp_root}" install 1.1.0 --codex >/dev/null
  run_with_env "${tmp_root}" activate 1.0.0 --codex >/dev/null

  local output
  output="$(run_with_env "${tmp_root}" list)"

  assert_contains "${output}" '1.0.0 (active)'
  assert_contains "${output}" '1.1.0'
  pass "${FUNCNAME[0]}"
}

test_install_codex_only() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex"
  local output
  output="$(run_with_env "${tmp_root}" install 1.0.0 --codex)"

  assert_contains "${output}" 'Target runtime: Codex'
  assert_contains "${output}" 'Installing version 1.0.0'
  assert_contains "${output}" 'Codex wiring complete'
  assert_exists "${tmp_root}/store/versions/1.0.0/manifest.json"
  assert_exists "${tmp_root}/store/versions/1.0.0/docs"
  assert_exists "${tmp_root}/store/versions/1.0.0/bin/mpt-skills"
  assert_symlink_target "${tmp_root}/bin/mpt-skills" "${tmp_root}/store/current/bin/mpt-skills"
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  assert_not_exists "${tmp_root}/claude/skills/mpt-ext-workflow-start-work"
  pass "${FUNCNAME[0]}"
}

test_install_claude_only() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/claude"
  local output
  output="$(run_with_env "${tmp_root}" install 1.1.0 --claude)"

  assert_contains "${output}" 'Target runtime: Claude'
  assert_contains "${output}" 'Claude wiring complete'
  assert_symlink_target "${tmp_root}/claude/skills/mpt-ext-tool-jira-workitem-ops" "${tmp_root}/store/current/skills/mpt-ext-tool-jira-workitem-ops"
  assert_not_exists "${tmp_root}/codex/skills/mpt-ext-tool-jira-workitem-ops"
  pass "${FUNCNAME[0]}"
}

test_install_all_and_preserve_non_managed_entries() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex/skills" "${tmp_root}/claude/skills"
  touch "${tmp_root}/codex/skills/custom-skill"
  touch "${tmp_root}/claude/skills/local-note"

  local output
  output="$(run_with_env "${tmp_root}" install 2.0.0 --all)"

  assert_contains "${output}" 'Target runtimes: Codex and Claude'
  assert_contains "${output}" 'Codex wiring complete'
  assert_contains "${output}" 'Claude wiring complete'
  assert_exists "${tmp_root}/codex/skills/custom-skill"
  assert_exists "${tmp_root}/claude/skills/local-note"
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  assert_symlink_target "${tmp_root}/claude/skills/mpt-ext-tool-jira-workitem-ops" "${tmp_root}/store/current/skills/mpt-ext-tool-jira-workitem-ops"
  pass "${FUNCNAME[0]}"
}

test_install_auto_detects_available_runtimes() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex" "${tmp_root}/claude"

  local output
  output="$(run_with_env "${tmp_root}" install 2.1.0)"

  assert_contains "${output}" 'Target runtimes: Codex and Claude'
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  assert_symlink_target "${tmp_root}/claude/skills/mpt-ext-tool-jira-workitem-ops" "${tmp_root}/store/current/skills/mpt-ext-tool-jira-workitem-ops"
  pass "${FUNCNAME[0]}"
}

test_activate_switches_current_version() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex"
  run_with_env "${tmp_root}" install 1.0.0 --codex >/dev/null
  run_with_env "${tmp_root}" install 1.1.0 --codex >/dev/null

  local output
  output="$(run_with_env "${tmp_root}" activate 1.0.0 --codex)"

  assert_contains "${output}" 'Activating installed version 1.0.0'
  assert_symlink_target "${tmp_root}/store/current" "${tmp_root}/store/versions/1.0.0"

  local help_output
  help_output="$(run_with_env "${tmp_root}" --help)"
  assert_contains "${help_output}" '1.0.0'
  pass "${FUNCNAME[0]}"
}

test_deactivate_removes_runtime_links_only() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex" "${tmp_root}/claude"
  run_with_env "${tmp_root}" install 1.0.0 --all >/dev/null

  local output
  output="$(run_with_env "${tmp_root}" deactivate --all)"

  assert_contains "${output}" 'Target runtimes: Codex and Claude'
  assert_contains "${output}" 'Codex links removed'
  assert_contains "${output}" 'Claude links removed'
  assert_not_exists "${tmp_root}/codex/skills/mpt-ext-workflow-start-work"
  assert_not_exists "${tmp_root}/claude/skills/mpt-ext-tool-jira-workitem-ops"
  assert_exists "${tmp_root}/store/current"
  assert_exists "${tmp_root}/store/versions/1.0.0/manifest.json"
  pass "${FUNCNAME[0]}"
}

test_deactivate_auto_detects_available_runtimes() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex" "${tmp_root}/claude"
  run_with_env "${tmp_root}" install 1.0.0 --all >/dev/null

  local output
  output="$(run_with_env "${tmp_root}" deactivate)"

  assert_contains "${output}" 'Target runtimes: Codex and Claude'
  assert_contains "${output}" 'Codex links removed'
  assert_contains "${output}" 'Claude links removed'
  assert_not_exists "${tmp_root}/codex/skills/mpt-ext-workflow-start-work"
  assert_not_exists "${tmp_root}/claude/skills/mpt-ext-tool-jira-workitem-ops"
  assert_exists "${tmp_root}/store/current"
  pass "${FUNCNAME[0]}"
}

test_remove_all_cleans_install_root_and_runtime_links() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex" "${tmp_root}/claude"
  run_with_env "${tmp_root}" install 1.0.0 --all >/dev/null

  local output
  output="$(run_with_env "${tmp_root}" remove --all)"

  assert_contains "${output}" 'Target runtimes: Codex and Claude'
  assert_contains "${output}" 'Codex links removed'
  assert_contains "${output}" 'Claude links removed'
  assert_contains "${output}" 'Removed user command'
  assert_contains "${output}" 'Removed install root'
  assert_not_exists "${tmp_root}/codex/skills/mpt-ext-workflow-start-work"
  assert_not_exists "${tmp_root}/claude/skills/mpt-ext-tool-jira-workitem-ops"
  assert_not_exists "${tmp_root}/store"
  assert_not_exists "${tmp_root}/bin/mpt-skills"
  pass "${FUNCNAME[0]}"
}

test_installed_command_is_invokable_as_mpt_skills() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex"
  run_with_env "${tmp_root}" install 3.0.0 --codex >/dev/null

  local output
  output="$(
    env \
      PATH="${tmp_root}/bin:${PATH}" \
      MPT_EXTENSION_SKILLS_HOME="${tmp_root}/store" \
      CODEX_SKILLS_DIR="${tmp_root}/codex/skills" \
      CLAUDE_SKILLS_DIR="${tmp_root}/claude/skills" \
      MPT_SKILLS_BIN_DIR="${tmp_root}/bin" \
      mpt-skills --help
  )"

  assert_contains "${output}" 'Usage:'
  assert_contains "${output}" 'mpt-skills install <version>'
  assert_contains "${output}" '3.0.0'
  pass "${FUNCNAME[0]}"
}

main() {
  chmod +x "${SCRIPT_PATH}"

  test_help_without_install
  TESTS_RUN=$((TESTS_RUN + 1))
  test_list_without_install
  TESTS_RUN=$((TESTS_RUN + 1))
  test_list_marks_active_version
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_codex_only
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_claude_only
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_all_and_preserve_non_managed_entries
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_auto_detects_available_runtimes
  TESTS_RUN=$((TESTS_RUN + 1))
  test_activate_switches_current_version
  TESTS_RUN=$((TESTS_RUN + 1))
  test_deactivate_removes_runtime_links_only
  TESTS_RUN=$((TESTS_RUN + 1))
  test_deactivate_auto_detects_available_runtimes
  TESTS_RUN=$((TESTS_RUN + 1))
  test_remove_all_cleans_install_root_and_runtime_links
  TESTS_RUN=$((TESTS_RUN + 1))
  test_installed_command_is_invokable_as_mpt_skills
  TESTS_RUN=$((TESTS_RUN + 1))

  printf '[DONE] %s tests passed\n' "${TESTS_RUN}"
}

main "$@"
