"""Behavioral layer on top of HumanCursor's SystemCursor.

SystemCursor already gives organic curved movement (Bezier knots +
distortion jitter + a random easing tween, see humancursor's own source).
What it doesn't give us is human-like *behavior* around those movements:
skewed reaction times, fatigue, idle drift, occasional mistakes, and a
non-uniform choice distribution. That's all handled here; HumanCursor is
only ever asked to move the cursor.
"""

import random
import time

import pyautogui
from humancursor import SystemCursor

import config


class Humanizer:
    def __init__(self):
        self.cursor = SystemCursor()
        self._session_start = time.monotonic()
        self._last_choice = None
        self._streak_len = 0

    # ---------------------------------------------------------------- timing
    def _session_fraction_elapsed(self):
        elapsed = time.monotonic() - self._session_start
        return min(elapsed / (config.SESSION_HOURS * 3600), 1.0)

    def _fatigue_multiplier(self):
        frac = self._session_fraction_elapsed()
        base = 1 + frac * (config.FATIGUE_MAX_MULTIPLIER - 1)
        return max(0.5, base + random.gauss(0, config.FATIGUE_JITTER))

    def sample_delay(self):
        """Inter-click delay: lognormal draw, right-skewed, scaled by fatigue."""
        raw = random.lognormvariate(config.DELAY_MU, config.DELAY_SIGMA)
        delay = raw * self._fatigue_multiplier()
        return min(max(delay, config.DELAY_MIN), config.DELAY_MAX)

    @staticmethod
    def _scaled_move_duration():
        """Mirror humancursor's own random.uniform(0.5, 2.0) draw, compressed
        by SPEED. Curve shape (knots/offsets/distortion) is generated inside
        SystemCursor.move_to itself and is never touched here."""
        return random.uniform(0.5, 2.0) / config.SPEED

    # ------------------------------------------------------------- movement
    def move_to(self, point):
        self.cursor.move_to(list(point), duration=self._scaled_move_duration())

    def idle_drift(self):
        """Small aimless movement between rounds instead of a parked cursor.
        Returns the drift target, or None if no drift happened this round."""
        if random.random() > config.IDLE_DRIFT_PROB:
            return None
        x, y = pyautogui.position()
        dx = random.randint(-config.IDLE_DRIFT_RADIUS, config.IDLE_DRIFT_RADIUS)
        dy = random.randint(-config.IDLE_DRIFT_RADIUS, config.IDLE_DRIFT_RADIUS)
        target = (max(0, x + dx), max(0, y + dy))
        self.move_to(target)
        return target

    def maybe_take_break(self):
        """Rare multi-minute break. Returns break length in seconds, or None."""
        if random.random() > config.BREAK_PROB:
            return None
        length = random.uniform(config.BREAK_MIN_SECONDS, config.BREAK_MAX_SECONDS)
        time.sleep(length)
        return length

    # --------------------------------------------------------- click target
    def _landing_point(self, button_name):
        """Point within a button's box, gaussian-weighted toward center."""
        b = config.BUTTONS[button_name]
        cx, cy = b["center"]
        half_w, half_h = b["width"] / 2, b["height"] / 2
        stdev_x = half_w * config.CLICK_SPREAD_FRACTION
        stdev_y = half_h * config.CLICK_SPREAD_FRACTION
        while True:
            x = random.gauss(cx, stdev_x)
            y = random.gauss(cy, stdev_y)
            if abs(x - cx) <= half_w and abs(y - cy) <= half_h:
                return (int(x), int(y))

    # -------------------------------------------------------------- choice
    def choose(self):
        """Next choice: biased weights with occasional streaks, not uniform."""
        if (
            self._last_choice
            and self._streak_len < config.STREAK_MAX_LEN
            and random.random() < config.STREAK_CONTINUE_PROB
        ):
            choice = self._last_choice
            self._streak_len += 1
        else:
            names, weights = zip(*config.CHOICE_BASE_WEIGHTS.items())
            choice = random.choices(names, weights=weights)[0]
            self._streak_len = 1 if choice == self._last_choice else 0
        self._last_choice = choice
        return choice

    # --------------------------------------------------------- click round
    def click_button(self, button_name):
        """Move to and click a button, occasionally with a human slip
        (overshoot+correction, misclick+recovery, double-click).
        Returns a list of event dicts for logging."""
        events = []
        target = self._landing_point(button_name)

        if random.random() < config.OVERSHOOT_PROB:
            overshoot = (
                target[0] + random.randint(-config.OVERSHOOT_MAX_PX, config.OVERSHOOT_MAX_PX),
                target[1] + random.randint(-config.OVERSHOOT_MAX_PX, config.OVERSHOOT_MAX_PX),
            )
            self.move_to(overshoot)
            events.append({"event": "overshoot", "x": overshoot[0], "y": overshoot[1]})
            self.move_to(target)
            events.append({"event": "correction", "x": target[0], "y": target[1]})
        else:
            self.move_to(target)

        if random.random() < config.MISCLICK_PROB:
            wrong_name = random.choice([b for b in config.BUTTONS if b != button_name])
            wrong_point = self._landing_point(wrong_name)
            self.move_to(wrong_point)
            pyautogui.click()
            events.append({
                "event": "misclick", "choice": wrong_name,
                "x": wrong_point[0], "y": wrong_point[1],
            })
            self.move_to(target)

        pyautogui.click(target[0], target[1])
        events.append({"event": "click", "choice": button_name, "x": target[0], "y": target[1]})

        if random.random() < config.DOUBLE_CLICK_PROB:
            time.sleep(random.uniform(0.05, 0.15))
            pyautogui.click(target[0], target[1])
            events.append({
                "event": "double_click", "choice": button_name,
                "x": target[0], "y": target[1],
            })

        return events
