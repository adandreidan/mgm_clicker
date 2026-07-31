"""Configuration for the rock-paper-scissors soak test.

Everything that controls timing, coordinates, or behavioral tuning lives
here so the rest of the code never hardcodes a number.
"""

# --- Screen coordinates ------------------------------------------------------
# Update these to match your game window. Run `python3 find_coords.py` and
# hover over each button to read off its x,y.
#
# These are ABSOLUTE SCREEN PIXELS, not page/DOM coordinates, so they go
# stale if anything about the window changes: browser window moved or
# resized, page zoom level changed, fullscreen vs windowed toggled, a
# responsive layout reflowing the buttons, or the OS display-scaling
# setting changing. Fix the browser window's size, position, and zoom
# for the whole session BEFORE running find_coords.py, and don't touch
# them again until the soak test finishes -- a resize mid-session will
# silently make every subsequent click land in the wrong place.
#
# radius is the clickable button's on-screen radius in pixels (buttons are
# circular). Measure it by hovering find_coords.py's cursor over the
# center, then over the visible edge, and taking the pixel distance.
BUTTONS = {
    "rock":     {"center": (859, 289), "radius": 60},
    "paper":    {"center": (766, 432), "radius": 60},
    "scissors": {"center": (955, 427), "radius": 60},
}

# Screen bounds, top-left to bottom-right. Used to keep idle drift (and
# anything else that nudges the cursor around) from wandering toward a
# physical screen corner, which would trip pyautogui's FAILSAFE.
SCREEN_MIN = (0, 0)
SCREEN_MAX = (1727, 1116)

# --- Speed --------------------------------------------------------------------
# humancursor's SystemCursor.move_to samples a travel duration of
# random.uniform(0.5, 2.0) seconds per move, regardless of pixel distance,
# and that duration is fully decoupled from curve shape (knots, offsets,
# distortion all live in humancursor's own randomizer and are never touched
# here). So SPEED just divides the sampled duration -> mean travel time
# drops but the relative spread (min/max ratio) and the curve shape are
# untouched. SPEED=1.0 reproduces stock humancursor timing.
SPEED = 8.0

# --- Session ------------------------------------------------------------------
SESSION_HOURS = 5.0

# --- Inter-click delay (hard cooldown + lognormal human jitter) ----------------
# The game itself needs ANIMATION_COOLDOWN_SECONDS after a click before it
# will register the next one -- this is a functional requirement, not a
# behavioral tuning knob. Clicking sooner risks a missed/desynced round.
#
# On top of that guaranteed floor, human reaction/decision time is
# right-skewed (most rounds react quickly once the animation clears, with
# an occasional longer pause), so the *jitter* added above the cooldown is
# drawn from a lognormal, not random.uniform -- a flat histogram is the
# easiest thing in the world to detect. Total delay = cooldown + jitter,
# so it can never fall below the cooldown (no clipping artifacts, since
# lognormal draws are always >= 0).
ANIMATION_COOLDOWN_SECONDS = 5.0
DELAY_JITTER_MU = -1.2      # ln-space mean -> median jitter ~= 0.30s
DELAY_JITTER_SIGMA = 0.6    # ln-space stdev -> controls the right-skew/tail
DELAY_MAX = 20.0            # hard cap on cooldown + jitter combined, seconds

# --- Fatigue --------------------------------------------------------------------
# Delays drift longer as the session goes on: a linear ramp on session
# progress, applied as a multiplier on top of the jitter draw (not the
# fixed animation cooldown -- that stays constant), plus a little noise
# so the ramp itself isn't a perfectly straight line.
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
# Landing point is sampled anywhere inside the button's circle: angle is
# uniform, radial distance is radius * random()**CLICK_CENTER_BIAS.
#   exponent 0.5  -> uniform-by-area (fills the whole circle evenly)
#   exponent 1.0  -> linear falloff, noticeably weighted toward center
#   exponent >1.5 -> tight cluster near center
# Lower this for a large button where you want clicks spread across more
# of its area; raise it for a small button where you want to stay safely
# away from the edge.
CLICK_CENTER_BIAS = 0.7

# Cap the sampled radius at this fraction of the true button radius, so a
# click never lands right on (or past) the edge of the hit area. Kept
# fairly conservative (rather than e.g. 0.9) because the measured radius
# above is itself an approximation -- this leaves margin for that error.
CLICK_MAX_RADIUS_FRACTION = 0.75

# When a round repeats the same button as the previous round, this is the
# chance the cursor just stays where it is (small in-place jitter, no
# deliberate travel) instead of re-traveling to a fresh point -- a real
# player often rests the cursor on a button they keep re-picking. The
# remaining (1 - this) fraction of repeats still travels normally, so
# staying put isn't the only thing that happens on a repeat either.
SAME_BUTTON_STAY_PROB = 0.55
STAY_JITTER_PX = 6   # max in-place pixel jitter when staying put

# --- Choice distribution & streaks -----------------------------------------------------
# Not uniform 33/33/33: biased toward paper, plus a strong chance to
# "stick" with the previous choice for several rounds before rerolling
# (streaky, like a real player who keeps repeating a pick).
CHOICE_BASE_WEIGHTS = {"rock": 0.25, "paper": 0.50, "scissors": 0.25}
STREAK_CONTINUE_PROB = 0.875  # chance to repeat the previous choice
STREAK_MAX_LEN = 16           # cap on consecutive repeats before forcing a reroll

# --- Logging -----------------------------------------------------------------------------
LOG_DIR = "logs"
