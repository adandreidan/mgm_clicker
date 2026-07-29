"""Configuration for the rock-paper-scissors soak test.

Everything that controls timing, coordinates, or behavioral tuning lives
here so the rest of the code never hardcodes a number.
"""

# --- Screen coordinates ------------------------------------------------------
# Update these to match your game window. Find them with:
#   python3 -c "import pyautogui, time; time.sleep(3); print(pyautogui.position())"
# hover the mouse over each button center during the 3s pause.
#
# width/height are the clickable button's on-screen size in pixels; the
# humanizer uses them to keep simulated click points inside the button.
BUTTONS = {
    "rock":     {"center": (600, 700), "width": 120, "height": 120},
    "paper":    {"center": (760, 700), "width": 120, "height": 120},
    "scissors": {"center": (920, 700), "width": 120, "height": 120},
}

# --- Speed --------------------------------------------------------------------
# humancursor's SystemCursor.move_to samples a travel duration of
# random.uniform(0.5, 2.0) seconds per move, regardless of pixel distance,
# and that duration is fully decoupled from curve shape (knots, offsets,
# distortion all live in humancursor's own randomizer and are never touched
# here). So SPEED just divides the sampled duration -> mean travel time
# drops but the relative spread (min/max ratio) and the curve shape are
# untouched. SPEED=1.0 reproduces stock humancursor timing.
SPEED = 3.0

# --- Session ------------------------------------------------------------------
SESSION_HOURS = 5.0

# --- Inter-click delay (lognormal, not uniform) --------------------------------
# Human reaction/decision time is right-skewed: most rounds click quickly,
# with an occasional long tail (hesitation, distraction). A flat uniform
# histogram is trivially distinguishable from real timing data.
#   median delay = exp(DELAY_MU)
DELAY_MU = -0.6        # ln-space mean -> median ~= 0.55s
DELAY_SIGMA = 0.5      # ln-space stdev -> controls the right-skew/tail weight
DELAY_MIN = 0.15       # hard floor, seconds
DELAY_MAX = 8.0        # hard cap, seconds (clip the extreme tail)

# --- Fatigue --------------------------------------------------------------------
# Delays drift longer as the session goes on: a linear ramp on session
# progress, applied as a multiplier on top of the lognormal draw, plus a
# little noise so the ramp itself isn't a perfectly straight line.
FATIGUE_MAX_MULTIPLIER = 1.8   # multiplier reached at the end of the session
FATIGUE_JITTER = 0.15          # stdev of gaussian noise added to the multiplier

# --- Idle cursor drift ------------------------------------------------------------
# Small movement between rounds instead of parking the cursor dead still.
IDLE_DRIFT_PROB = 0.6      # probability of a drift move happening each round
IDLE_DRIFT_RADIUS = 40     # px, max drift distance from current cursor position

# --- Breaks -----------------------------------------------------------------------
BREAK_PROB = 0.004                # probability per round of taking a break
BREAK_MIN_SECONDS = 60
BREAK_MAX_SECONDS = 240

# --- Imperfections -----------------------------------------------------------------
OVERSHOOT_PROB = 0.06       # move past the target then correct
OVERSHOOT_MAX_PX = 25
MISCLICK_PROB = 0.02        # click the wrong button, then recover
DOUBLE_CLICK_PROB = 0.03    # accidental double-click on the intended button

# --- Click landing point -------------------------------------------------------------
# Fraction of the button's half-width/half-height used as the gaussian
# stdev for where inside the button the click actually lands (weighted
# toward center, resampled if it falls outside the button).
CLICK_SPREAD_FRACTION = 0.28

# --- Choice distribution & streaks -----------------------------------------------------
# Not uniform 33/33/33: a mild bias plus a chance to "stick" with the
# previous choice for a few rounds (streaky, like real players).
CHOICE_BASE_WEIGHTS = {"rock": 0.38, "paper": 0.31, "scissors": 0.31}
STREAK_CONTINUE_PROB = 0.18   # chance to repeat the previous choice
STREAK_MAX_LEN = 4            # cap on consecutive repeats before forcing a reroll

# --- Logging -----------------------------------------------------------------------------
LOG_DIR = "logs"
