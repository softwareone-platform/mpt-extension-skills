#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMMAND_NAME="$(basename "$0")"
GITHUB_REPOSITORY_NAME="softwareone-platform/mpt-extension-skills"
RELEASES_BASE_URL="${MPT_SKILLS_RELEASES_BASE_URL:-https://github.com/${GITHUB_REPOSITORY_NAME}/releases}"
GITHUB_API_BASE_URL="${MPT_SKILLS_GITHUB_API_BASE_URL:-https://api.github.com/repos/${GITHUB_REPOSITORY_NAME}}"

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

cleanup_release_tmp_files() {
  rm -rf "${MPT_SKILLS_TMP_ARCHIVE:-}" "${MPT_SKILLS_TMP_EXTRACT_DIR:-}"
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
  ${COMMAND_NAME} install --version <version> [--codex | --claude | --all]
  ${COMMAND_NAME} install --path <local-repo> [--codex | --claude | --all]
  ${COMMAND_NAME} activate <version> [--codex | --claude | --all]
  ${COMMAND_NAME} deactivate [--codex | --claude | --all]
  ${COMMAND_NAME} upgrade [--version <version>] [--codex | --claude | --all]
  ${COMMAND_NAME} remove --all
  ${COMMAND_NAME} list
  ${COMMAND_NAME} --help

Commands:
  install --version <version>  Install a package from a GitHub release
  install --path <local-repo>  Install from a local repository checkout
  activate <version>          Switch current to an installed version
  deactivate                  Remove managed runtime skill links
  upgrade                     Install and activate a GitHub release
  remove --all                Remove installed package files and managed links
  list                        Show installed versions and available GitHub releases
  --help                      Show this help

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
  MPT_SKILLS_BIN_DIR         Directory where the user-facing mpt-extensions-skills command is linked
                             Default: \$HOME/.local/bin

$(current_version_block)
EOF
}

repo_commit() {
  local source_dir="${1:-${REPO_ROOT}}"
  if git -C "${source_dir}" rev-parse --verify HEAD >/dev/null 2>&1; then
    git -C "${source_dir}" rev-parse --short HEAD
  else
    printf 'unknown'
  fi
}

source_commit_for_manifest() {
  local source_dir="$1"
  local source_type="$2"
  local manifest_commit=""

  if [[ "${source_type}" == "release" && -f "${source_dir}/manifest.json" ]]; then
    manifest_commit="$(sed -n 's/.*"source_commit"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "${source_dir}/manifest.json" | head -n 1)"
  fi

  if [[ -n "${manifest_commit}" ]]; then
    printf '%s' "${manifest_commit}"
  else
    repo_commit "${source_dir}"
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
      -name 'mpt-ext-*' -exec test -f '{}/SKILL.md' ';' -print | wc -l | tr -d ' '
  )"
  printf '%s' "${count}"
}

write_manifest() {
  local version="$1"
  local version_dir="$2"
  local source_dir="$3"
  local source_type="$4"
  local installed_at
  installed_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  log_info "Writing manifest.json for version ${version}"
  cat > "${version_dir}/manifest.json" <<EOF
{
  "name": "mpt-extension-skills",
  "version": "${version}",
  "installed_at": "${installed_at}",
  "source_repo": "${GITHUB_REPOSITORY_NAME}",
  "source_commit": "$(source_commit_for_manifest "${source_dir}" "${source_type}")",
  "source_type": "${source_type}"
}
EOF
}

install_cli_command() {
  local version_dir="$1"
  local source_dir="$2"
  local bin_dir="${version_dir}/bin"

  log_info "Installing package CLI into ${bin_dir}"
  mkdir -p "${bin_dir}"
  cp "${source_dir}/scripts/mpt-extensions-skills.sh" "${bin_dir}/mpt-extensions-skills"
  chmod +x "${bin_dir}/mpt-extensions-skills"
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

parse_upgrade_selection() {
  UPGRADE_VERSION=""
  local runtime_args=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version)
        if [[ $# -lt 2 || -z "$2" || "$2" == --* ]]; then
          echo "Missing upgrade version after --version" >&2
          usage
          exit 1
        fi
        if [[ -n "${UPGRADE_VERSION}" ]]; then
          echo "Upgrade version specified more than once" >&2
          exit 1
        fi
        UPGRADE_VERSION="$2"
        shift 2
        ;;
      --codex|--claude|--all)
        runtime_args+=("$1")
        shift
        ;;
      *)
        echo "Unknown option: $1" >&2
        usage
        exit 1
        ;;
    esac
  done

  if [[ "${#runtime_args[@]}" -eq 0 ]]; then
    parse_runtime_selection
  else
    parse_runtime_selection "${runtime_args[@]}"
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
    if [[ ! -f "${skill_dir}/SKILL.md" ]]; then
      continue
    fi
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

  if [[ -L "${COMMAND_BIN_DIR}/mpt-extensions-skills" || -f "${COMMAND_BIN_DIR}/mpt-extensions-skills" ]]; then
    log_info "Removing user command ${COMMAND_BIN_DIR}/mpt-extensions-skills"
    rm -f "${COMMAND_BIN_DIR}/mpt-extensions-skills"
    log_done "Removed user command"
  fi

  if [[ -d "${INSTALL_ROOT}" || -L "${INSTALL_ROOT}" ]]; then
    log_info "Removing install root ${INSTALL_ROOT}"
    rm -rf "${INSTALL_ROOT}"
    log_done "Removed install root"
  fi
}

require_source_package() {
  local source_dir="$1"
  local missing=0

  for path in scripts/mpt-extensions-skills.sh skills standards knowledge docs; do
    if [[ ! -e "${source_dir}/${path}" ]]; then
      echo "Package source is missing required path: ${source_dir}/${path}" >&2
      missing=1
    fi
  done

  if [[ "${missing}" -ne 0 ]]; then
    exit 1
  fi
}

copy_package_files() {
  local source_dir="$1"
  local version_dir="$2"

  log_info "Copying skills/"
  cp -R "${source_dir}/skills" "${version_dir}/skills"

  log_info "Copying standards/"
  cp -R "${source_dir}/standards" "${version_dir}/standards"

  log_info "Copying knowledge/"
  cp -R "${source_dir}/knowledge" "${version_dir}/knowledge"

  log_info "Copying docs/"
  cp -R "${source_dir}/docs" "${version_dir}/docs"
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
  log_info "Linking user command mpt-extensions-skills into ${COMMAND_BIN_DIR}"
  ln -sfn "${INSTALL_ROOT}/current/bin/mpt-extensions-skills" "${COMMAND_BIN_DIR}/mpt-extensions-skills"
  log_done "Command available as ${COMMAND_BIN_DIR}/mpt-extensions-skills"

  activate_selected_runtimes
  log_done "Version ${version} is now active"
}

install_from_source() {
  local version="$1"
  local source_dir="$2"
  local source_type="$3"
  local version_dir="${INSTALL_ROOT}/versions/${version}"

  if [[ -e "${version_dir}" ]]; then
    if [[ "${version}" == "local" ]]; then
      log_info "Replacing existing local installation"
      rm -rf "${version_dir}"
    else
      log_info "Version ${version} is already installed"
      activate_version "${version}"
      return
    fi
  fi

  require_source_package "${source_dir}"
  log_info "Installing version ${version} from ${source_type}"
  ensure_install_root

  log_info "Creating version directory ${version_dir}"
  mkdir -p "${version_dir}"

  copy_package_files "${source_dir}" "${version_dir}"

  write_manifest "${version}" "${version_dir}" "${source_dir}" "${source_type}"
  install_cli_command "${version_dir}" "${source_dir}"
  log_done "Installed package files for version ${version}"

  activate_version "${version}"
}

release_asset_name() {
  local version="$1"
  printf 'mpt-extension-skills-%s.tar.gz' "${version}"
}

download_release_package() {
  local version="$1"
  local destination="$2"
  local asset_name
  asset_name="$(release_asset_name "${version}")"

  if [[ -n "${MPT_SKILLS_RELEASE_ASSET_DIR:-}" ]]; then
    local local_asset="${MPT_SKILLS_RELEASE_ASSET_DIR}/${asset_name}"
    if [[ ! -f "${local_asset}" ]]; then
      echo "Release asset not found: ${local_asset}" >&2
      exit 1
    fi
    log_info "Using local release asset ${local_asset}"
    cp "${local_asset}" "${destination}"
    return
  fi

  local url="${RELEASES_BASE_URL}/download/${version}/${asset_name}"
  log_info "Downloading release asset ${url}"
  curl -LsSf "${url}" -o "${destination}"
}

install_release_version() {
  local version="$1"
  local archive
  local extract_dir
  archive="$(mktemp)"
  extract_dir="$(mktemp -d)"
  MPT_SKILLS_TMP_ARCHIVE="${archive}"
  MPT_SKILLS_TMP_EXTRACT_DIR="${extract_dir}"
  trap cleanup_release_tmp_files EXIT INT TERM

  download_release_package "${version}" "${archive}"
  tar -xzf "${archive}" -C "${extract_dir}"
  install_from_source "${version}" "${extract_dir}" "release"
  cleanup_release_tmp_files
  trap - EXIT INT TERM
}

install_local_path() {
  local source_dir="$1"

  if [[ ! -d "${source_dir}" ]]; then
    echo "Local repository path does not exist: ${source_dir}" >&2
    exit 1
  fi

  install_from_source "local" "${source_dir}" "local"
}

latest_release_version() {
  if [[ -n "${MPT_SKILLS_LATEST_VERSION:-}" ]]; then
    printf '%s\n' "${MPT_SKILLS_LATEST_VERSION}"
    return
  fi

  local latest_url="${GITHUB_API_BASE_URL}/releases/latest"
  local response
  if ! response="$(curl -LsSf "${latest_url}")"; then
    log_warn "latest_release_version could not fetch release metadata from ${latest_url}"
    return
  fi

  # The CLI avoids requiring jq, so this intentionally uses a small sed parser
  # for GitHub's tag_name field and reports a warning if the response shape changes.
  local tag
  tag="$(printf '%s' "${response}" | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"

  if [[ -z "${tag}" ]]; then
    log_warn "latest_release_version could not parse tag_name from GitHub response"
  fi

  printf '%s\n' "${tag}"
}

current_installed_version() {
  if [[ -f "${INSTALL_ROOT}/current/manifest.json" ]]; then
    sed -n 's/.*"version": "\(.*\)".*/\1/p' "${INSTALL_ROOT}/current/manifest.json" | head -n 1
  fi
}

upgrade_to_latest() {
  local latest_version
  latest_version="$(latest_release_version)"

  if [[ -z "${latest_version}" ]]; then
    echo "Unable to resolve latest release version" >&2
    exit 1
  fi

  local current_version
  current_version="$(current_installed_version)"

  if [[ "${current_version}" == "${latest_version}" ]]; then
    log_done "Already on latest version (${current_version})"
    return
  fi

  if [[ -n "${current_version}" ]]; then
    log_info "Upgrading from ${current_version} to ${latest_version}"
  else
    log_info "Installing latest version ${latest_version}"
  fi

  install_release_version "${latest_version}"
}

sort_versions_desc() {
  awk '
    {
      original = $0
      normalized = original
      sub(/^v/, "", normalized)
      split(normalized, parts, /[.-]/)
      printf "%010d.%010d.%010d\t%s\n", parts[1] + 0, parts[2] + 0, parts[3] + 0, original
    }
  ' | sort -r | cut -f2-
}

latest_available_versions() {
  sort_versions_desc | head -n 10
}

available_release_versions() {
  if [[ -n "${MPT_SKILLS_AVAILABLE_RELEASES:-}" ]]; then
    printf '%s\n' "${MPT_SKILLS_AVAILABLE_RELEASES}" | tr ', ' '\n' | sed '/^$/d' | latest_available_versions
    return
  fi

  if [[ -n "${MPT_SKILLS_RELEASE_ASSET_DIR:-}" ]]; then
    find "${MPT_SKILLS_RELEASE_ASSET_DIR}" -maxdepth 1 -type f \
      -name 'mpt-extension-skills-*.tar.gz' -exec basename {} \; \
      | sed 's/^mpt-extension-skills-//; s/\.tar\.gz$//' \
      | latest_available_versions
    return
  fi

  local releases_url="${GITHUB_API_BASE_URL}/releases"
  local response
  if ! response="$(curl -LsSf "${releases_url}")"; then
    log_warn "list could not fetch release metadata from ${releases_url}"
    return
  fi

  if command -v jq >/dev/null 2>&1; then
    printf '%s' "${response}" | jq -r '.[].tag_name // empty' 2>/dev/null | latest_available_versions || true
    return
  fi

  printf '%s' "${response}" \
    | tr '{' '\n' \
    | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
    | latest_available_versions
}

version_is_installed() {
  local version="$1"
  [[ -d "${INSTALL_ROOT}/versions/${version}" ]]
}

list_installed() {
  local current_version=""
  local installed_versions=""
  if [[ -f "${INSTALL_ROOT}/current/manifest.json" ]]; then
    current_version="$(sed -n 's/.*"version": "\(.*\)".*/\1/p' "${INSTALL_ROOT}/current/manifest.json" | head -n 1)"
  fi

  if [[ -d "${INSTALL_ROOT}/versions" ]]; then
    installed_versions="$(find "${INSTALL_ROOT}/versions" -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | sort_versions_desc)"
  fi

  if [[ -z "${installed_versions}" ]]; then
    echo "No installed versions found"
  else
    echo "Installed versions:"
    while IFS= read -r version; do
      if [[ -n "${current_version}" && "${version}" == "${current_version}" ]]; then
        printf '  %s (active)\n' "${version}"
      else
        printf '  %s\n' "${version}"
      fi
    done <<< "${installed_versions}"
  fi

  local available_versions
  available_versions="$(available_release_versions)"

  if [[ -z "${available_versions}" ]]; then
    echo "No available GitHub releases found"
    exit 0
  fi

  echo "Available GitHub releases:"
  local printed=0
  while IFS= read -r version; do
    if [[ -z "${version}" ]]; then
      continue
    fi
    if version_is_installed "${version}"; then
      printf '  %s (installed)\n' "${version}"
    else
      printf '  %s\n' "${version}"
    fi
    printed=$((printed + 1))
  done <<< "${available_versions}"

  if [[ "${printed}" -eq 0 ]]; then
    echo "No available GitHub releases found"
  fi
}

main() {
  if [[ $# -lt 1 ]]; then
    usage
    exit 1
  fi

  case "$1" in
    install)
      if [[ $# -lt 2 || $# -gt 6 ]]; then
        usage
        exit 1
      fi
      case "$2" in
        --version)
          if [[ $# -lt 3 ]]; then
            usage
            exit 1
          fi
          local_version="$3"
          shift 3
          parse_runtime_selection "$@"
          log_runtime_selection
          install_release_version "${local_version}"
          ;;
        --path)
          if [[ $# -lt 3 ]]; then
            usage
            exit 1
          fi
          local_path="$3"
          shift 3
          parse_runtime_selection "$@"
          log_runtime_selection
          install_local_path "${local_path}"
          ;;
        *)
          usage
          exit 1
          ;;
      esac
      ;;
    __install-from-source)
      if [[ $# -lt 3 || $# -gt 6 ]]; then
        usage
        exit 1
      fi
      local_version="$2"
      local_path="$3"
      shift 3
      parse_runtime_selection "$@"
      log_runtime_selection
      install_from_source "${local_version}" "${local_path}" "${MPT_SKILLS_INSTALL_SOURCE_TYPE:-local-checkout}"
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
    upgrade)
      if [[ $# -gt 6 ]]; then
        usage
        exit 1
      fi
      shift
      parse_upgrade_selection "$@"
      log_runtime_selection
      if [[ -n "${UPGRADE_VERSION}" ]]; then
        install_release_version "${UPGRADE_VERSION}"
      else
        upgrade_to_latest
      fi
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
