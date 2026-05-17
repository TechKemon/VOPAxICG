from __future__ import annotations

from collections.abc import Iterable

from course_list import course_list

from myca_recsys.models import Course


class CatalogError(ValueError):
    pass


def load_courses(raw_courses: Iterable[dict] | None = None) -> list[Course]:
    courses = [Course.model_validate(item) for item in (raw_courses or course_list)]
    _validate_unique_ids(courses)
    return courses


def _validate_unique_ids(courses: list[Course]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for course in courses:
        if course.id in seen:
            duplicates.add(course.id)
        seen.add(course.id)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise CatalogError(f"duplicate course ids: {joined}")
