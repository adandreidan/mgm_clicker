"""Behavioral layer on top of HumanCursor's SystemCursor.

SystemCursor already gives organic curved movement (Bezier knots +
distortion jitter + a random easing tween, see humancursor's own source).
What it doesn't give us is human-like *behavior* around those movements:
skewed reaction times, fatigue, idle drift, occasional mistakes, and a
non-uniform choice distribution. That's all handled here; HumanCursor is
only ever asked to move the cursor.
"""

import math
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
        self._last_clicked = None

    # ---------------------------------------------------------------- timing
    def _session_fraction_elapsed(self):
        elapsed = time.monotonic() - self._session_start
        return min(elapsed / (config.SESSION_HOURS * 3600), 1.0)

    def _fatigue_multiplier(self):
        frac = self._session_fraction_elapsed()
        base = 1 + frac * (config.FATIGUE_MAX_MULTIPLIER - 1)
        return max(0.5, base + random.gauss(0, config.FATIGUE_JITTER))

    def sample_delay(self):
        """Inter-click delay: a fixed game-animation cooldown, plus a
        right-skewed lognormal jitter (scaled by fatigue) on top. The
        cooldown is a hard floor by construction -- jitter is always >= 0,
        so there's no clipping artifact piling draws up at a boundary."""
        jitter = random.lognormvariate(config.DELAY_JITTER_MU, config.DELAY_JITTER_SIGMA)
        delay = config.ANIMATION_COOLDOWN_SECONDS + jitter * self._fatigue_multiplier()
        return min(delay, config.DELAY_MAX)

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
        target = (
            min(max(x + dx, config.SCREEN_MIN[0]), config.SCREEN_MAX[0]),
            min(max(y + dy, config.SCREEN_MIN[1]), config.SCREEN_MAX[1]),
        )
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
        """Point within a button's circle: uniform angle, radius drawn from
        random()**CLICK_CENTER_BIAS so it's weighted toward center but still
        covers the whole button (see config.CLICK_CENTER_BIAS)."""
        b = config.BUTTONS[button_name]
        cx, cy = b["center"]
        max_r = b["radius"] * config.CLICK_MAX_RADIUS_FRACTION
        angle = random.uniform(0, 2 * math.pi)
        r = max_r * (random.random() ** config.CLICK_CENTER_BIAS)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        return (int(x), int(y))

    def _clamp_to_button(self, point, button_name):
        """Pull a point back inside the button's allowed click radius if a
        jitter step pushed it out."""
        b = config.BUTTONS[button_name]
        cx, cy = b["center"]
        max_r = b["radius"] * config.CLICK_MAX_RADIUS_FRACTION
        dx, dy = point[0] - cx, point[1] - cy
        dist = math.hypot(dx, dy)
        if dist <= max_r or dist == 0:
            return point
        scale = max_r / dist
        return (int(cx + dx * scale), int(cy + dy * scale))

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

        When this round repeats the same button as last time, sometimes
        stays put -- a small in-place jitter with no deliberate travel,
        like a real player resting the cursor on a button they keep
        picking -- rather than always re-traveling across it. The rest of
        the time it still travels to a freshly sampled point even though
        it's the same icon, so staying put isn't the only outcome either.

        Returns a list of event dicts for logging."""
        events = []
        same_as_last = button_name == self._last_clicked
        stay_put = same_as_last and random.random() < config.SAME_BUTTON_STAY_PROB

        if stay_put:
            cur_x, cur_y = pyautogui.position()
            jittered = (
                cur_x + random.randint(-config.STAY_JITTER_PX, config.STAY_JITTER_PX),
                cur_y + random.randint(-config.STAY_JITTER_PX, config.STAY_JITTER_PX),
            )
            target = self._clamp_to_button(jittered, button_name)
            pyautogui.moveTo(target[0], target[1])
            events.append({"event": "stay_adjust", "x": target[0], "y": target[1]})
        else:
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

        self._last_clicked = button_name
        return events
