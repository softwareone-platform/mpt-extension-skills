#!/usr/bin/env bash

set -euo pipefail

GITHUB_REPOSITORY_NAME="${MPT_SKILLS_GITHUB_REPOSITORY:-softwareone-platform/mpt-extension-skills}"
RELEASES_BASE_URL="${MPT_SKILLS_RELEASES_BASE_URL:-https://github.com/${GITHUB_REPOSITORY_NAME}/releases}"
GITHUB_API_BASE_URL="${MPT_SKILLS_GITHUB_API_BASE_URL:-https://api.github.com/repos/${GITHUB_REPOSITORY_NAME}}"
INSTALL_VERSION="${MPT_SKILLS_INSTALL_VERSION:-__MPT_SKILLS_RELEASE_VERSION__}"

log_info() {
  printf '[INFO] %s\n' "$*"
}

log_warn() {
  printf '[WARN] %s\n' "$*" >&2
}

cleanup_tmp_files() {
  rm -rf "${MPT_SKILLS_TMP_ARCHIVE:-}" "${MPT_SKILLS_TMP_EXTRACT_DIR:-}"
}

resolve_latest_version() {
  if [[ -n "${MPT_SKILLS_LATEST_VERSION:-}" ]]; then
    printf '%s\n' "${MPT_SKILLS_LATEST_VERSION}"
    return
  fi

  local response
  if ! response="$(curl -LsSf "${GITHUB_API_BASE_URL}/releases/latest")"; then
    log_warn "Unable to fetch latest release metadata from ${GITHUB_API_BASE_URL}"
    return
  fi

  local tag=""
  if command -v jq >/dev/null 2>&1; then
    tag="$(printf '%s' "${response}" | jq -r '.tag_name // empty' 2>/dev/null || true)"
  fi

  if [[ -z "${tag}" ]]; then
    tag="$(printf '%s' "${response}" | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
  fi

  if [[ -z "${tag}" ]]; then
    log_warn "Unable to parse latest release tag_name from GitHub response"
  fi

  printf '%s\n' "${tag}"
}

main() {
  local version="${INSTALL_VERSION}"
  if [[ $# -gt 0 && "$1" != --* ]]; then
    version="$1"
    shift
  fi

  if [[ "${version}" == "__MPT_SKILLS_RELEASE_VERSION__" || -z "${version}" ]]; then
    version="$(resolve_latest_version)"
  fi

  if [[ -z "${version}" ]]; then
    echo "Unable to resolve mpt-extension-skills release version" >&2
    exit 1
  fi

  local asset_name="mpt-extension-skills-${version}.tar.gz"
  local archive
  local extract_dir
  archive="$(mktemp)"
  extract_dir="$(mktemp -d)"
  MPT_SKILLS_TMP_ARCHIVE="${archive}"
  MPT_SKILLS_TMP_EXTRACT_DIR="${extract_dir}"
  trap cleanup_tmp_files EXIT INT TERM

  if [[ -n "${MPT_SKILLS_RELEASE_ASSET_DIR:-}" ]]; then
    log_info "Using local release asset ${MPT_SKILLS_RELEASE_ASSET_DIR}/${asset_name}"
    cp "${MPT_SKILLS_RELEASE_ASSET_DIR}/${asset_name}" "${archive}"
  else
    local url="${RELEASES_BASE_URL}/download/${version}/${asset_name}"
    log_info "Downloading ${url}"
    curl -LsSf "${url}" -o "${archive}"
  fi

  tar -xzf "${archive}" -C "${extract_dir}"
  MPT_SKILLS_INSTALL_SOURCE_TYPE="release" "${extract_dir}/scripts/mpt-extensions-skills.sh" __install-from-source "${version}" "${extract_dir}" "$@"
}

main "$@"
