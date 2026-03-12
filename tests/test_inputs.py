from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


from scripts.core.inputs import detect_publisher, load_inputs, normalize_entry


def test_detect_publisher_from_known_doi_prefixes():
    assert detect_publisher("10.1021/acs.est.6c01242") == "acs"
    assert detect_publisher("10.1038/ncomms14183") == "nature"
    assert detect_publisher("10.1126/science.ada1091") == "science"
    assert detect_publisher("10.1016/j.egypro.2017.09.579") == "sciencedirect"


def test_normalize_entry_extracts_doi_and_publisher_from_urls():
    entry = normalize_entry("https://doi.org/10.1038/ncomms14183")

    assert entry.publisher == "nature"
    assert entry.doi == "10.1038/ncomms14183"
    assert entry.kind == "doi"
    assert entry.canonical == "10.1038/ncomms14183"


def test_normalize_entry_preserves_article_urls():
    entry = normalize_entry("https://www.sciencedirect.com/science/article/pii/S1876610217346770")

    assert entry.publisher == "sciencedirect"
    assert entry.kind == "url"
    assert entry.article_url == "https://www.sciencedirect.com/science/article/pii/S1876610217346770"
    assert entry.canonical == "https://www.sciencedirect.com/science/article/pii/S1876610217346770"


def test_load_inputs_deduplicates_entries(tmp_path):
    source = tmp_path / "inputs.txt"
    source.write_text(
        "\n".join(
            [
                "10.1126/science.ada1091",
                "https://doi.org/10.1126/science.ada1091",
                "# comment",
                "10.1021/acs.est.6c01242",
            ]
        ),
        encoding="utf-8",
    )

    items = load_inputs([], source)

    assert [item.canonical for item in items] == [
        "10.1126/science.ada1091",
        "10.1021/acs.est.6c01242",
    ]
