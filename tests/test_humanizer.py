import math
import random

import pytest

import config
from humanizer import Humanizer


@pytest.fixture
def hz():
    random.seed(0)
    return Humanizer(session_hours=1)


def test_config_is_valid():
    config.validate()


@pytest.mark.parametrize("name", list(config.BUTTONS))
def test_landing_point_within_allowed_radius(hz, name):
    b = config.BUTTONS[name]
    max_r = b["radius"] * config.CLICK_MAX_RADIUS_FRACTION
    for _ in range(2000):
        x, y = hz._landing_point(name)
        # +1 for int() truncation
        assert math.hypot(x - b["center"][0], y - b["center"][1]) <= max_r + 1


def test_clamp_pulls_point_back_inside(hz):
    b = config.BUTTONS["rock"]
    far = (b["center"][0] + 1000, b["center"][1])
    x, y = hz._clamp_to_button(far, "rock")
    assert math.hypot(x - b["center"][0], y - b["center"][1]) <= b["radius"] * config.CLICK_MAX_RADIUS_FRACTION


def test_sample_delay_bounds(hz):
    for _ in range(2000):
        d = hz.sample_delay()
        assert config.ANIMATION_COOLDOWN_SECONDS <= d <= config.DELAY_MAX


def test_choose_returns_known_buttons(hz):
    assert {hz.choose() for _ in range(2000)} <= set(config.BUTTONS)


def test_streak_counter_never_exceeds_cap(hz):
    for _ in range(5000):
        hz.choose()
        assert hz._streak_len <= config.STREAK_MAX_LEN
