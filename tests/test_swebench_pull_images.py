import collections

from scripts.swebench_pull_images import collect_images, extract_image


def test_extract_image_prefers_explicit_field():
    row = {"docker_image": "swebench/foo", "image": "other"}
    assert extract_image(row, "image") == "other"


def test_extract_image_auto_detects_default_fields():
    row = {"docker_image": "swebench/bar"}
    assert extract_image(row, None) == "swebench/bar"


def test_extract_image_returns_none_for_missing():
    row = {"repo": "example"}
    assert extract_image(row, None) is None


def test_collect_images_counts_unique_images():
    rows = [
        {"docker_image": "img-a"},
        {"docker_image": "img-a"},
        {"docker_image": "img-b"},
        {"docker_image": ""},
    ]
    counts = collect_images(rows, None)
    assert isinstance(counts, collections.Counter)
    assert counts["img-a"] == 2
    assert counts["img-b"] == 1
    assert "" not in counts
