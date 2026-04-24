#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SCRIPT_PATH="${REPO_ROOT}/scripts/mpt-extensions-skills.sh"

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

assert_before() {
  local haystack="$1"
  local first="$2"
  local second="$3"
  local first_line
  local second_line
  first_line="$(printf '%s\n' "${haystack}" | awk -v needle="${first}" 'index($0, needle) { print NR; exit }')"
  second_line="$(printf '%s\n' "${haystack}" | awk -v needle="${second}" 'index($0, needle) { print NR; exit }')"
  [[ -n "${first_line}" ]] || fail "Expected output to contain: ${first}"
  [[ -n "${second_line}" ]] || fail "Expected output to contain: ${second}"
  [[ "${first_line}" -lt "${second_line}" ]] || fail "Expected ${first} before ${second}"
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

run_with_home_defaults() {
  local tmp_root="$1"
  shift
  env -i \
    HOME="${tmp_root}" \
    PATH="/usr/bin:/bin" \
    "${SCRIPT_PATH}" "$@"
}

create_release_asset() {
  local version="$1"
  local asset_dir="$2"
  local package_dir
  package_dir="$(mktemp -d)"

  mkdir -p "${asset_dir}" "${package_dir}/package"
  cp -R \
    "${REPO_ROOT}/scripts" \
    "${REPO_ROOT}/skills" \
    "${REPO_ROOT}/standards" \
    "${REPO_ROOT}/knowledge" \
    "${REPO_ROOT}/docs" \
    "${package_dir}/package/"
  cat > "${package_dir}/package/manifest.json" <<EOF
{
  "name": "mpt-extension-skills",
  "version": "${version}",
  "source_repo": "softwareone-platform/mpt-extension-skills",
  "source_commit": "release-test-commit",
  "source_type": "release"
}
EOF

  tar -C "${package_dir}/package" -czf "${asset_dir}/mpt-extension-skills-${version}.tar.gz" .
}

run_with_release_env() {
  local tmp_root="$1"
  local asset_dir="$2"
  local latest_version="$3"
  shift 3
  env \
    MPT_EXTENSION_SKILLS_HOME="${tmp_root}/store" \
    CODEX_SKILLS_DIR="${tmp_root}/codex/skills" \
    CLAUDE_SKILLS_DIR="${tmp_root}/claude/skills" \
    MPT_SKILLS_BIN_DIR="${tmp_root}/bin" \
    MPT_SKILLS_RELEASE_ASSET_DIR="${asset_dir}" \
    MPT_SKILLS_LATEST_VERSION="${latest_version}" \
    "${SCRIPT_PATH}" "$@"
}

install_release_for_test() {
  local tmp_root="$1"
  local version="$2"
  shift 2
  local asset_dir="${tmp_root}/assets"
  create_release_asset "${version}" "${asset_dir}"
  run_with_release_env "${tmp_root}" "${asset_dir}" "${version}" install --version "${version}" "$@"
}

test_help_without_install() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  local output
  output="$(run_with_env "${tmp_root}" --help)"

  assert_contains "${output}" 'Usage:'
  assert_contains "${output}" 'install --version <version>'
  assert_contains "${output}" 'install --path <local-repo>'
  if [[ "${output}" == *'install <version>'* ]]; then
    fail 'Deprecated install <version> form must not be shown in help'
  fi
  assert_contains "${output}" 'upgrade [--version <version>] [--codex | --claude | --all]'
  if [[ "${output}" == *'update [--codex | --claude | --all]'* ]]; then
    fail 'Deprecated update command must not be shown in help'
  fi
  assert_contains "${output}" 'Commands:'
  assert_contains "${output}" 'list                        Show installed versions and available GitHub releases'
  assert_contains "${output}" 'Environment overrides:'
  assert_contains "${output}" 'MPT_EXTENSION_SKILLS_HOME  Install root for versioned package contents'
  assert_contains "${output}" 'CODEX_SKILLS_DIR           Codex skills directory to wire during activation'
  assert_contains "${output}" 'CLAUDE_SKILLS_DIR          Claude skills directory to wire during activation'
  assert_contains "${output}" 'MPT_SKILLS_BIN_DIR         Directory where the user-facing mpt-extensions-skills command is linked'
  assert_contains "${output}" 'Default: $HOME/.codex/skills'
  assert_contains "${output}" 'Current installed version:'
  assert_contains "${output}" 'not installed'
  pass "${FUNCNAME[0]}"
}

test_list_without_install() {
  local tmp_root
  tmp_root="$(mktemp -d)"
  local asset_dir="${tmp_root}/assets"
  local version
  for version in 1.1.0 1.2.0 1.3.0 1.4.0 1.5.0 1.6.0 1.7.0 1.8.0 1.9.0 1.10.0 1.11.0 1.12.0; do
    create_release_asset "${version}" "${asset_dir}"
  done

  local output
  output="$(run_with_release_env "${tmp_root}" "${asset_dir}" "1.2.0" list)"

  assert_contains "${output}" 'No installed versions found'
  assert_contains "${output}" 'Available GitHub releases:'
  assert_contains "${output}" '1.3.0'
  assert_contains "${output}" '1.10.0'
  assert_contains "${output}" '1.12.0'
  assert_contains "${output}" '1.11.0'
  if [[ "${output}" == *'1.2.0'* ]]; then
    fail 'Expected list to show only the latest 10 available releases'
  fi
  assert_before "${output}" '1.12.0' '1.11.0'
  assert_before "${output}" '1.11.0' '1.10.0'
  assert_before "${output}" '1.10.0' '1.3.0'
  pass "${FUNCNAME[0]}"
}

test_list_treats_empty_versions_dir_as_no_install() {
  local tmp_root
  tmp_root="$(mktemp -d)"
  local asset_dir="${tmp_root}/assets"
  create_release_asset "1.2.0" "${asset_dir}"
  mkdir -p "${tmp_root}/store/versions"

  local output
  output="$(run_with_release_env "${tmp_root}" "${asset_dir}" "1.2.0" list)"

  assert_contains "${output}" 'No installed versions found'
  if [[ "${output}" == *'Installed versions:'* ]]; then
    fail 'Expected empty versions directory to skip Installed versions section'
  fi
  pass "${FUNCNAME[0]}"
}

test_list_marks_active_version() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex"
  install_release_for_test "${tmp_root}" 1.0.0 --codex >/dev/null
  install_release_for_test "${tmp_root}" 1.1.0 --codex >/dev/null
  install_release_for_test "${tmp_root}" 1.10.0 --codex >/dev/null
  run_with_env "${tmp_root}" activate 1.1.0 --codex >/dev/null

  local output
  local asset_dir="${tmp_root}/assets"
  create_release_asset "1.2.0" "${asset_dir}"
  create_release_asset "1.3.0" "${asset_dir}"
  create_release_asset "1.10.0" "${asset_dir}"

  output="$(run_with_release_env "${tmp_root}" "${asset_dir}" "1.2.0" list)"

  assert_contains "${output}" 'Installed versions:'
  assert_contains "${output}" '1.0.0'
  assert_contains "${output}" '1.1.0 (active)'
  assert_contains "${output}" '1.10.0'
  assert_before "${output}" '1.10.0' '1.1.0 (active)'
  assert_before "${output}" '1.1.0 (active)' '1.0.0'
  assert_contains "${output}" 'Available GitHub releases:'
  assert_contains "${output}" '1.2.0'
  assert_contains "${output}" '1.3.0'
  assert_contains "${output}" '1.10.0'
  assert_before "${output}" '1.10.0' '1.3.0'
  assert_before "${output}" '1.3.0' '1.2.0'
  pass "${FUNCNAME[0]}"
}

test_install_codex_only() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex"
  local output
  output="$(install_release_for_test "${tmp_root}" 1.0.0 --codex)"

  assert_contains "${output}" 'Target runtime: Codex'
  assert_contains "${output}" 'Installing version 1.0.0'
  assert_contains "${output}" 'Codex wiring complete'
  assert_exists "${tmp_root}/store/versions/1.0.0/manifest.json"
  assert_exists "${tmp_root}/store/versions/1.0.0/docs"
  assert_exists "${tmp_root}/store/versions/1.0.0/bin/mpt-extensions-skills"
  assert_symlink_target "${tmp_root}/bin/mpt-extensions-skills" "${tmp_root}/store/current/bin/mpt-extensions-skills"
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  assert_not_exists "${tmp_root}/claude/skills/mpt-ext-workflow-start-work"
  pass "${FUNCNAME[0]}"
}

test_install_from_release_asset() {
  local tmp_root
  tmp_root="$(mktemp -d)"
  local asset_dir="${tmp_root}/assets"
  create_release_asset "4.0.0" "${asset_dir}"

  mkdir -p "${tmp_root}/codex"
  local output
  output="$(run_with_release_env "${tmp_root}" "${asset_dir}" "4.0.0" install --version 4.0.0 --codex)"

  assert_contains "${output}" 'Using local release asset'
  assert_contains "${output}" 'Installing version 4.0.0 from release'
  assert_symlink_target "${tmp_root}/store/current" "${tmp_root}/store/versions/4.0.0"
  assert_exists "${tmp_root}/store/versions/4.0.0/bin/mpt-extensions-skills"
  assert_contains "$(sed -n 's/.*"source_commit": "\(.*\)".*/\1/p' "${tmp_root}/store/versions/4.0.0/manifest.json")" 'release-test-commit'
  assert_contains "$(sed -n 's/.*"source_type": "\(.*\)".*/\1/p' "${tmp_root}/store/versions/4.0.0/manifest.json")" 'release'
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  pass "${FUNCNAME[0]}"
}

test_install_from_local_path_uses_local_version() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex"
  local output
  output="$(run_with_env "${tmp_root}" install --path "${REPO_ROOT}" --codex)"

  assert_contains "${output}" 'Installing version local from local'
  assert_symlink_target "${tmp_root}/store/current" "${tmp_root}/store/versions/local"
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  pass "${FUNCNAME[0]}"
}

test_install_from_local_path_uses_local_git_commit() {
  local tmp_root
  tmp_root="$(mktemp -d)"
  local source_dir="${tmp_root}/source"
  mkdir -p "${source_dir}/scripts" "${source_dir}/skills/mpt-ext-demo" "${source_dir}/standards" "${source_dir}/knowledge" "${source_dir}/docs" "${tmp_root}/codex"

  cp "${SCRIPT_PATH}" "${source_dir}/scripts/mpt-extensions-skills.sh"
  printf '# Demo\n' > "${source_dir}/skills/mpt-ext-demo/SKILL.md"
  printf '{"source_commit": "stale-release-commit"}\n' > "${source_dir}/manifest.json"

  git -C "${source_dir}" init >/dev/null
  git -C "${source_dir}" config user.email test@example.com
  git -C "${source_dir}" config user.name Test
  git -C "${source_dir}" add . >/dev/null
  git -C "${source_dir}" commit -m init >/dev/null

  local expected_commit
  expected_commit="$(git -C "${source_dir}" rev-parse --short HEAD)"

  run_with_env "${tmp_root}" install --path "${source_dir}" --codex >/dev/null

  local actual_commit
  actual_commit="$(sed -n 's/.*"source_commit": "\(.*\)".*/\1/p' "${tmp_root}/store/versions/local/manifest.json")"
  local actual_type
  actual_type="$(sed -n 's/.*"source_type": "\(.*\)".*/\1/p' "${tmp_root}/store/versions/local/manifest.json")"

  [[ "${actual_commit}" == "${expected_commit}" ]] || fail "Expected local source_commit ${expected_commit}, got ${actual_commit}"
  [[ "${actual_type}" == "local" ]] || fail "Expected local source_type, got ${actual_type}"
  pass "${FUNCNAME[0]}"
}

test_upgrade_installs_latest_release() {
  local tmp_root
  tmp_root="$(mktemp -d)"
  local asset_dir="${tmp_root}/assets"
  create_release_asset "4.1.0" "${asset_dir}"

  mkdir -p "${tmp_root}/codex"
  install_release_for_test "${tmp_root}" 4.0.0 --codex >/dev/null

  local output
  output="$(run_with_release_env "${tmp_root}" "${asset_dir}" "4.1.0" upgrade --codex)"

  assert_contains "${output}" 'Upgrading from 4.0.0 to 4.1.0'
  assert_symlink_target "${tmp_root}/store/current" "${tmp_root}/store/versions/4.1.0"
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  pass "${FUNCNAME[0]}"
}

test_upgrade_without_runtime_flags_uses_auto_detection() {
  local tmp_root
  tmp_root="$(mktemp -d)"
  local asset_dir="${tmp_root}/assets"
  create_release_asset "4.1.0" "${asset_dir}"

  mkdir -p "${tmp_root}/codex"
  install_release_for_test "${tmp_root}" 4.0.0 --codex >/dev/null

  local output
  output="$(run_with_release_env "${tmp_root}" "${asset_dir}" "4.1.0" upgrade)"

  assert_contains "${output}" 'Target runtime: Codex'
  assert_contains "${output}" 'Upgrading from 4.0.0 to 4.1.0'
  assert_symlink_target "${tmp_root}/store/current" "${tmp_root}/store/versions/4.1.0"
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  pass "${FUNCNAME[0]}"
}

test_upgrade_installs_specific_release() {
  local tmp_root
  tmp_root="$(mktemp -d)"
  local asset_dir="${tmp_root}/assets"
  create_release_asset "4.1.0" "${asset_dir}"
  create_release_asset "4.2.0" "${asset_dir}"

  mkdir -p "${tmp_root}/codex"
  install_release_for_test "${tmp_root}" 4.0.0 --codex >/dev/null

  local output
  output="$(run_with_release_env "${tmp_root}" "${asset_dir}" "4.2.0" upgrade --codex --version 4.1.0)"

  assert_contains "${output}" 'Installing version 4.1.0 from release'
  assert_symlink_target "${tmp_root}/store/current" "${tmp_root}/store/versions/4.1.0"
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  assert_not_exists "${tmp_root}/store/versions/4.2.0"
  pass "${FUNCNAME[0]}"
}

test_upgrade_rejects_missing_version_value() {
  local tmp_root
  tmp_root="$(mktemp -d)"
  local asset_dir="${tmp_root}/assets"
  create_release_asset "4.1.0" "${asset_dir}"

  local output
  if output="$(run_with_release_env "${tmp_root}" "${asset_dir}" "4.1.0" upgrade --version --codex 2>&1)"; then
    fail 'Expected upgrade --version --codex to fail'
  fi

  assert_contains "${output}" 'Missing upgrade version after --version'
  assert_not_exists "${tmp_root}/store/versions/4.1.0"
  pass "${FUNCNAME[0]}"
}

test_install_claude_only() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/claude"
  local output
  output="$(install_release_for_test "${tmp_root}" 1.1.0 --claude)"

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
  output="$(install_release_for_test "${tmp_root}" 2.0.0 --all)"

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
  output="$(install_release_for_test "${tmp_root}" 2.1.0)"

  assert_contains "${output}" 'Target runtimes: Codex and Claude'
  assert_symlink_target "${tmp_root}/codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/store/current/skills/mpt-ext-workflow-start-work"
  assert_symlink_target "${tmp_root}/claude/skills/mpt-ext-tool-jira-workitem-ops" "${tmp_root}/store/current/skills/mpt-ext-tool-jira-workitem-ops"
  pass "${FUNCNAME[0]}"
}

test_install_uses_default_home_runtime_dirs() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/.codex" "${tmp_root}/.claude"

  local output
  local asset_dir="${tmp_root}/assets"
  create_release_asset "2.2.0" "${asset_dir}"
  output="$(
    env -i \
      HOME="${tmp_root}" \
      PATH="/usr/bin:/bin" \
      MPT_SKILLS_RELEASE_ASSET_DIR="${asset_dir}" \
      MPT_SKILLS_LATEST_VERSION="2.2.0" \
      "${SCRIPT_PATH}" install --version 2.2.0
  )"

  assert_contains "${output}" 'Target runtimes: Codex and Claude'
  assert_symlink_target "${tmp_root}/.codex/skills/mpt-ext-workflow-start-work" "${tmp_root}/.mpt-extension-skills/current/skills/mpt-ext-workflow-start-work"
  assert_symlink_target "${tmp_root}/.claude/skills/mpt-ext-tool-jira-workitem-ops" "${tmp_root}/.mpt-extension-skills/current/skills/mpt-ext-tool-jira-workitem-ops"
  assert_symlink_target "${tmp_root}/.local/bin/mpt-extensions-skills" "${tmp_root}/.mpt-extension-skills/current/bin/mpt-extensions-skills"
  pass "${FUNCNAME[0]}"
}

test_activate_switches_current_version() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex"
  install_release_for_test "${tmp_root}" 1.0.0 --codex >/dev/null
  install_release_for_test "${tmp_root}" 1.1.0 --codex >/dev/null

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
  install_release_for_test "${tmp_root}" 1.0.0 --all >/dev/null

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
  install_release_for_test "${tmp_root}" 1.0.0 --all >/dev/null

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
  install_release_for_test "${tmp_root}" 1.0.0 --all >/dev/null

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
  assert_not_exists "${tmp_root}/bin/mpt-extensions-skills"
  pass "${FUNCNAME[0]}"
}

test_installed_command_is_invokable_as_mpt_extensions_skills() {
  local tmp_root
  tmp_root="$(mktemp -d)"

  mkdir -p "${tmp_root}/codex"
  install_release_for_test "${tmp_root}" 3.0.0 --codex >/dev/null

  local output
  output="$(
    env \
      PATH="${tmp_root}/bin:${PATH}" \
      MPT_EXTENSION_SKILLS_HOME="${tmp_root}/store" \
      CODEX_SKILLS_DIR="${tmp_root}/codex/skills" \
      CLAUDE_SKILLS_DIR="${tmp_root}/claude/skills" \
      MPT_SKILLS_BIN_DIR="${tmp_root}/bin" \
      mpt-extensions-skills --help
  )"

  assert_contains "${output}" 'Usage:'
  assert_contains "${output}" 'mpt-extensions-skills install --version <version>'
  assert_contains "${output}" '3.0.0'
  pass "${FUNCNAME[0]}"
}

main() {
  chmod +x "${SCRIPT_PATH}"

  test_help_without_install
  TESTS_RUN=$((TESTS_RUN + 1))
  test_list_without_install
  TESTS_RUN=$((TESTS_RUN + 1))
  test_list_treats_empty_versions_dir_as_no_install
  TESTS_RUN=$((TESTS_RUN + 1))
  test_list_marks_active_version
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_codex_only
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_from_release_asset
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_from_local_path_uses_local_version
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_from_local_path_uses_local_git_commit
  TESTS_RUN=$((TESTS_RUN + 1))
  test_upgrade_installs_latest_release
  TESTS_RUN=$((TESTS_RUN + 1))
  test_upgrade_without_runtime_flags_uses_auto_detection
  TESTS_RUN=$((TESTS_RUN + 1))
  test_upgrade_installs_specific_release
  TESTS_RUN=$((TESTS_RUN + 1))
  test_upgrade_rejects_missing_version_value
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_claude_only
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_all_and_preserve_non_managed_entries
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_auto_detects_available_runtimes
  TESTS_RUN=$((TESTS_RUN + 1))
  test_install_uses_default_home_runtime_dirs
  TESTS_RUN=$((TESTS_RUN + 1))
  test_activate_switches_current_version
  TESTS_RUN=$((TESTS_RUN + 1))
  test_deactivate_removes_runtime_links_only
  TESTS_RUN=$((TESTS_RUN + 1))
  test_deactivate_auto_detects_available_runtimes
  TESTS_RUN=$((TESTS_RUN + 1))
  test_remove_all_cleans_install_root_and_runtime_links
  TESTS_RUN=$((TESTS_RUN + 1))
  test_installed_command_is_invokable_as_mpt_extensions_skills
  TESTS_RUN=$((TESTS_RUN + 1))

  printf '[DONE] %s tests passed\n' "${TESTS_RUN}"
}

main "$@"
