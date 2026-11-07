import pytest

from soundpad.utils.formatting import format_clock, format_duration


@pytest.mark.parametrize(
    "ms,expected",
    [
        (0, "0:00.0"),
        (1500, "0:01.5"),
        (61_000, "1:01.0"),
        (3_661_000, "1:01:01"),
        (-5, "0:00.0"),
    ],
)
def test_format_duration(ms, expected):
    assert format_duration(ms) == expected


def test_format_clock():
    assert format_clock(65_000) == "01:05"
    assert format_clock(-1) == "00:00"
