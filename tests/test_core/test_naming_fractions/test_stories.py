"""Tests for the sharing stories' bank: every story fills all its slots, and only those."""

import string

from core.naming_fractions.stories import GROUP_STORIES, WHOLE_STORIES


def _slots(text: str) -> set[str]:
    """Return the names of the slots in ``text``, such as {"people", "total"}."""
    return {name for _, name, _, _ in string.Formatter().parse(text) if name is not None}


def test_stories_fill_their_slots() -> None:
    """
    A group story has slots for the people, how many objects and their name; a whole story's
    setup has one for the people, and a whole that comes cut says into how many parts.
    """
    wrong = [
        story for story in GROUP_STORIES if _slots(story.setup) != {"people", "total", "objects"}
    ]
    wrong += [
        story
        for story in WHOLE_STORIES
        if _slots(story.setup) != {"people"}
        or _slots(story.cut) != ({"total"} if story.precut else set())
    ]
    assert wrong == []
