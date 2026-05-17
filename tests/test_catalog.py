import pytest

from myca_recsys.catalog import CatalogError, load_courses


def test_load_courses_validates_unique_ids():
    raw = [
        {"id": "C001", "title": "One", "description": "A", "keywords": [], "domains": {}},
        {"id": "C001", "title": "Two", "description": "B", "keywords": [], "domains": {}},
    ]

    with pytest.raises(CatalogError):
        load_courses(raw)


def test_load_courses_rejects_missing_title():
    raw = [{"id": "C001", "title": "", "description": "A", "keywords": [], "domains": {}}]

    with pytest.raises(ValueError):
        load_courses(raw)
