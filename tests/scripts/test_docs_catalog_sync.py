"""Keep the standards/ and knowledge/ catalogs in sync with both indexes.

Every ``standards/*.md`` and ``knowledge/*.md`` file must be linked from both
``AGENTS.md`` (so agents can discover it) and ``README.md`` (the human index).
This closes the gap where a shared doc exists on disk and in one index but is
invisible in the other.
"""
import pytest

from helpers import REPO_ROOT

INDEX_FILES = ["AGENTS.md", "README.md"]
DOC_DIRS = ["standards", "knowledge"]


def _doc_paths():
    for doc_dir in DOC_DIRS:
        for path in sorted((REPO_ROOT / doc_dir).glob("*.md")):
            yield doc_dir, path.name


_CASES = list(_doc_paths())
_INDEX_TEXT = {name: (REPO_ROOT / name).read_text(encoding="utf-8") for name in INDEX_FILES}


@pytest.mark.parametrize(
    ("index_file", "doc_dir", "doc_name"),
    [(index, doc_dir, doc_name) for index in INDEX_FILES for doc_dir, doc_name in _CASES],
    ids=lambda v: v,
)
def test_doc_is_listed_in_index(index_file, doc_dir, doc_name):
    link = f"{doc_dir}/{doc_name}"
    assert link in _INDEX_TEXT[index_file], (
        f"{index_file} does not link {link}; add it to the catalog so the doc is discoverable"
    )
