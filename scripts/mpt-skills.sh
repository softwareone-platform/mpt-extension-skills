#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMMAND_NAME="$(basename "$0")"

INSTALL_ROOT="${MPT_EXTENSION_SKILLS_HOME:-${HOME}/.mpt-extension-skills}"
CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-${HOME}/.codex/skills}"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-${HOME}/.claude/skills}"
COMMAND_BIN_DIR="${MPT_SKILLS_BIN_DIR:-${HOME}/.local/bin}"

log_info() {
  printf '[INFO] %s\n' "$*"
}

log_warn() {
  printf '[WARN] %s\n' "$*" >&2
}

log_done() {
  printf '[DONE] %s\n' "$*"
}

current_version_block() {
  if [[ -f "${INSTALL_ROOT}/current/manifest.json" ]]; then
    local version
    version="$(sed -n 's/.*"version": "\(.*\)".*/\1/p' "${INSTALL_ROOT}/current/manifest.json" | head -n 1)"
    if [[ -n "${version}" ]]; then
      printf 'Current installed version:\n  %s\n' "${version}"
      return
    fi
  fi

  printf 'Current installed version:\n  not installed\n'
}

usage() {
  cat <<EOF
Usage:
  ${COMMAND_NAME} install <version> [--codex | --claude | --all]
  ${COMMAND_NAME} activate <version> [--codex | --claude | --all]
  ${COMMAND_NAME} deactivate [--codex | --claude | --all]
  ${COMMAND_NAME} remove --all
  ${COMMAND_NAME} list
  ${COMMAND_NAME} --help

Runtime targeting:
  No runtime flag  Auto-detect installed runtimes and wire only those
  --codex         Wire only Codex
  --claude        Wire only Claude
  --all           Wire both Codex and Claude

Environment overrides:
  MPT_EXTENSION_SKILLS_HOME  Install root for versioned package contents
                             Default: \$HOME/.mpt-extension-skills
  CODEX_SKILLS_DIR           Codex skills directory to wire during activation
                             Default: \$HOME/.codex/skills
  CLAUDE_SKILLS_DIR          Claude skills directory to wire during activation
                             Default: \$HOME/.claude/skills
  MPT_SKILLS_BIN_DIR         Directory where the user-facing mpt-skills command is linked
                             Default: \$HOME/.local/bin

$(current_version_block)
EOF
}

repo_commit() {
  if git -C "${REPO_ROOT}" rev-parse --verify HEAD >/dev/null 2>&1; then
    git -C "${REPO_ROOT}" rev-parse --short HEAD
  else
    printf 'unknown'
  fi
}

ensure_install_root() {
  mkdir -p "${INSTALL_ROOT}/versions"
}

ensure_command_bin_dir() {
  mkdir -p "${COMMAND_BIN_DIR}"
}

runtime_root_for_dir() {
  dirname "$1"
}

runtime_is_available() {
  local runtime_dir="$1"
  local runtime_root
  runtime_root="$(runtime_root_for_dir "${runtime_dir}")"
  [[ -d "${runtime_dir}" || -d "${runtime_root}" ]]
}

skill_count() {
  local count
  count="$(
    find "${INSTALL_ROOT}/current/skills" -maxdepth 1 -mindepth 1 -type d \
      -name 'mpt-ext-*' | wc -l | tr -d ' '
  )"
  printf '%s' "${count}"
}

write_manifest() {
  local version="$1"
  local version_dir="$2"
  local installed_at
  installed_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  log_info "Writing manifest.json for version ${version}"
  cat > "${version_dir}/manifest.json" <<EOF
{
  "name": "mpt-extension-skills",
  "version": "${version}",
  "installed_at": "${installed_at}",
  "source_repo": "softwareone-platform/mpt-extension-skills",
  "source_commit": "$(repo_commit)"
}
EOF
}

install_cli_command() {
  local version_dir="$1"
  local bin_dir="${version_dir}/bin"

  log_info "Installing package CLI into ${bin_dir}"
  mkdir -p "${bin_dir}"
  cp "${REPO_ROOT}/scripts/mpt-skills.sh" "${bin_dir}/mpt-skills"
  chmod +x "${bin_dir}/mpt-skills"
  log_done "Installed package CLI files"
}

parse_runtime_selection() {
  TARGET_CODEX=0
  TARGET_CLAUDE=0
  RUNTIME_MODE="auto"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --codex)
        TARGET_CODEX=1
        RUNTIME_MODE="explicit"
        ;;
      --claude)
        TARGET_CLAUDE=1
        RUNTIME_MODE="explicit"
        ;;
      --all)
        TARGET_CODEX=1
        TARGET_CLAUDE=1
        RUNTIME_MODE="explicit"
        ;;
      *)
        echo "Unknown option: $1" >&2
        usage
        exit 1
        ;;
    esac
    shift
  done

  if [[ "${RUNTIME_MODE}" == "auto" ]]; then
    if runtime_is_available "${CODEX_SKILLS_DIR}"; then
      TARGET_CODEX=1
    fi
    if runtime_is_available "${CLAUDE_SKILLS_DIR}"; then
      TARGET_CLAUDE=1
    fi
  fi
}

log_runtime_selection() {
  if [[ "${TARGET_CODEX}" -eq 1 && "${TARGET_CLAUDE}" -eq 1 ]]; then
    log_info "Target runtimes: Codex and Claude"
  elif [[ "${TARGET_CODEX}" -eq 1 ]]; then
    log_info "Target runtime: Codex"
  elif [[ "${TARGET_CLAUDE}" -eq 1 ]]; then
    log_info "Target runtime: Claude"
  else
    log_warn "No runtime selected or detected. The package will be installed without wiring Codex or Claude links."
  fi
}

refresh_runtime_links() {
  local runtime_name="$1"
  local runtime_dir="$2"

  log_info "Preparing ${runtime_name} runtime directory at ${runtime_dir}"
  mkdir -p "${runtime_dir}"

  log_info "Removing existing managed skill links from ${runtime_name}"
  find "${runtime_dir}" -maxdepth 1 -mindepth 1 \
    -name 'mpt-ext-*' -exec rm -rf {} +

  local linked=0
  local skill_dir
  while IFS= read -r -d '' skill_dir; do
    ln -sfn "${skill_dir}" "${runtime_dir}/$(basename "${skill_dir}")"
    linked=$((linked + 1))
    log_info "Linked $(basename "${skill_dir}") into ${runtime_name}"
  done < <(
    find "${INSTALL_ROOT}/current/skills" -maxdepth 1 -mindepth 1 -type d \
      -name 'mpt-ext-*' -print0
  )

  log_done "${runtime_name} wiring complete (${linked} skills linked)"
}

remove_runtime_links() {
  local runtime_name="$1"
  local runtime_dir="$2"

  if [[ ! -d "${runtime_dir}" ]]; then
    log_info "Skipping ${runtime_name}: runtime directory does not exist at ${runtime_dir}"
    return
  fi

  log_info "Removing existing managed skill links from ${runtime_name}"
  find "${runtime_dir}" -maxdepth 1 -mindepth 1 \
    -name 'mpt-ext-*' -exec rm -rf {} +
  log_done "${runtime_name} links removed"
}

activate_selected_runtimes() {
  if [[ "${TARGET_CODEX}" -eq 1 ]]; then
    refresh_runtime_links "Codex" "${CODEX_SKILLS_DIR}"
  fi

  if [[ "${TARGET_CLAUDE}" -eq 1 ]]; then
    refresh_runtime_links "Claude" "${CLAUDE_SKILLS_DIR}"
  fi

  if [[ "${TARGET_CODEX}" -eq 0 && "${TARGET_CLAUDE}" -eq 0 ]]; then
    log_warn "Skipped runtime wiring because no compatible runtime directories were detected."
    log_warn "Use --codex, --claude, or --all to force runtime wiring."
  fi
}

deactivate_selected_runtimes() {
  if [[ "${TARGET_CODEX}" -eq 1 ]]; then
    remove_runtime_links "Codex" "${CODEX_SKILLS_DIR}"
  fi

  if [[ "${TARGET_CLAUDE}" -eq 1 ]]; then
    remove_runtime_links "Claude" "${CLAUDE_SKILLS_DIR}"
  fi

  if [[ "${TARGET_CODEX}" -eq 0 && "${TARGET_CLAUDE}" -eq 0 ]]; then
    log_warn "Skipped runtime deactivation because no compatible runtime directories were detected."
    log_warn "Use --codex, --claude, or --all to force runtime deactivation."
  fi
}

remove_all() {
  TARGET_CODEX=0
  TARGET_CLAUDE=0

  if runtime_is_available "${CODEX_SKILLS_DIR}"; then
    TARGET_CODEX=1
  fi
  if runtime_is_available "${CLAUDE_SKILLS_DIR}"; then
    TARGET_CLAUDE=1
  fi

  log_runtime_selection
  deactivate_selected_runtimes

  if [[ -L "${COMMAND_BIN_DIR}/mpt-skills" || -f "${COMMAND_BIN_DIR}/mpt-skills" ]]; then
    log_info "Removing user command ${COMMAND_BIN_DIR}/mpt-skills"
    rm -f "${COMMAND_BIN_DIR}/mpt-skills"
    log_done "Removed user command"
  fi

  if [[ -d "${INSTALL_ROOT}" || -L "${INSTALL_ROOT}" ]]; then
    log_info "Removing install root ${INSTALL_ROOT}"
    rm -rf "${INSTALL_ROOT}"
    log_done "Removed install root"
  fi
}

activate_version() {
  local version="$1"
  local version_dir="${INSTALL_ROOT}/versions/${version}"

  if [[ ! -d "${version_dir}" ]]; then
    echo "Installed version not found: ${version}" >&2
    exit 1
  fi

  log_info "Activating installed version ${version}"
  ln -sfn "${version_dir}" "${INSTALL_ROOT}/current"
  log_done "Updated current symlink to ${version_dir}"

  ensure_command_bin_dir
  log_info "Linking user command mpt-skills into ${COMMAND_BIN_DIR}"
  ln -sfn "${INSTALL_ROOT}/current/bin/mpt-skills" "${COMMAND_BIN_DIR}/mpt-skills"
  log_done "Command available as ${COMMAND_BIN_DIR}/mpt-skills"

  activate_selected_runtimes
  log_done "Version ${version} is now active"
}

install_version() {
  local version="$1"
  local version_dir="${INSTALL_ROOT}/versions/${version}"

  if [[ -e "${version_dir}" ]]; then
    echo "Version already installed: ${version}" >&2
    exit 1
  fi

  log_info "Installing version ${version} from local repository checkout"
  ensure_install_root

  log_info "Creating version directory ${version_dir}"
  mkdir -p "${version_dir}"

  log_info "Copying skills/"
  cp -R "${REPO_ROOT}/skills" "${version_dir}/skills"

  log_info "Copying standards/"
  cp -R "${REPO_ROOT}/standards" "${version_dir}/standards"

  log_info "Copying knowledge/"
  cp -R "${REPO_ROOT}/knowledge" "${version_dir}/knowledge"

  log_info "Copying docs/"
  cp -R "${REPO_ROOT}/docs" "${version_dir}/docs"

  write_manifest "${version}" "${version_dir}"
  install_cli_command "${version_dir}"
  log_done "Installed package files for version ${version}"

  activate_version "${version}"
}

list_installed() {
  if [[ ! -d "${INSTALL_ROOT}/versions" ]]; then
    echo "No installed versions found"
    exit 0
  fi

  local current_version=""
  if [[ -f "${INSTALL_ROOT}/current/manifest.json" ]]; then
    current_version="$(sed -n 's/.*"version": "\(.*\)".*/\1/p' "${INSTALL_ROOT}/current/manifest.json" | head -n 1)"
  fi

  while IFS= read -r version; do
    if [[ -n "${current_version}" && "${version}" == "${current_version}" ]]; then
      printf '%s (active)\n' "${version}"
    else
      printf '%s\n' "${version}"
    fi
  done < <(find "${INSTALL_ROOT}/versions" -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | sort)
}

main() {
  if [[ $# -lt 1 ]]; then
    usage
    exit 1
  fi

  case "$1" in
    install)
      if [[ $# -lt 2 || $# -gt 5 ]]; then
        usage
        exit 1
      fi
      local_version="$2"
      shift 2
      parse_runtime_selection "$@"
      log_runtime_selection
      install_version "${local_version}"
      ;;
    activate)
      if [[ $# -lt 2 || $# -gt 5 ]]; then
        usage
        exit 1
      fi
      local_version="$2"
      shift 2
      parse_runtime_selection "$@"
      log_runtime_selection
      ensure_install_root
      activate_version "${local_version}"
      ;;
    deactivate)
      if [[ $# -gt 4 ]]; then
        usage
        exit 1
      fi
      shift
      parse_runtime_selection "$@"
      log_runtime_selection
      deactivate_selected_runtimes
      ;;
    remove)
      if [[ $# -ne 2 || "$2" != "--all" ]]; then
        usage
        exit 1
      fi
      remove_all
      ;;
    list)
      list_installed
      ;;
    --help|-h|help)
      usage
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
