# mgm_clicker — agent adaptation notes

Audience: an LLM agent (e.g. Claude Code) asked to port this to a new
device/game window. Not written for human onboarding — it's a spec +
procedure. Terse on purpose.

## What this is

RPS soak-test bot. Clicks rock/paper/scissors buttons continuously for
`SESSION_HOURS`, with human-like timing/movement, to stress-test a game
and its own bot-detection logic simultaneously. Logs every action to CSV
for replay against detection logic.

## File map

| File | Role |
|---|---|
| `config.py` | ALL tunables. Read this first, edit this to port to a new machine. |
| `humanizer.py` | `Humanizer` class — timing, movement, choice logic, imperfections. Wraps `humancursor.SystemCursor`; never calls `SystemCursor.click_on` (see Gotchas). |
| `main.py` | Run loop, CSV logger, Ctrl+C handling. CLI flag `--minutes N` overrides `config.SESSION_HOURS` for short tests without editing config. |
| `find_coords.py` | Standalone: prints live cursor position at 10Hz. Used to measure button coords/radius by hovering, no click required. |
| `logs/session_<timestamp>.csv` | Output. Schema below. |

## Porting to a new device/game — procedure

Run in this order. Do not skip steps 3/5/7 — they're the actual
device-specific state; everything else is optional tuning.

1. **Deps**: `pip3 install -r requirements.txt`.
   Pillow is required by `pyscreeze` (pyautogui's screenshot backend) but is
   not reliably auto-installed as its dependency on newer Python — on a
   fresh Python 3.14 install here, `pyautogui.screenshot()` raised
   `PyAutoGUIException` importing pyscreeze until Pillow was installed
   manually. Confirm with `python3 -c "import pyautogui, PIL"`.

2. **macOS permissions**: grant **Accessibility** to whatever process
   runs Python (Terminal/iTerm/VS Code) — System Settings → Privacy &
   Security → Accessibility. Required for `pyautogui` to move/click.
   Grant **Screen Recording** too if screenshot-based verification is
   wanted (`pyautogui.screenshot()` fails with "could not create image
   from display" without it — distinct permission from Accessibility).
   Linux/Windows: no equivalent gate normally, but Wayland can block
   synthetic input entirely — verify a plain `pyautogui.moveTo` works first.

3. **Screen bounds**: `python3 -c "import pyautogui; print(pyautogui.size())"`
   → set `config.SCREEN_MIN = (0, 0)` and `config.SCREEN_MAX = (width-1, height-1)`.
   Used only to keep `idle_drift` from approaching a physical screen
   corner, which trips `pyautogui.FAILSAFE` (intentional kill switch, do
   not disable — `main.py` sets `pyautogui.FAILSAFE = True`).

4. **Fix the window layout** before measuring anything: game window
   position, size, and browser zoom must stay constant for the entire
   session. Coordinates below are absolute screen pixels, not DOM/page
   coordinates — they silently go stale on resize/zoom/fullscreen
   toggle/display-scaling change, with no error, just missed clicks.

5. **Measure buttons**: run `python3 find_coords.py`, hover each
   button's center then its visible edge, compute radius = pixel
   distance. Update `config.BUTTONS`:
   ```python
   BUTTONS = {
       "rock":     {"center": (x, y), "radius": r},
       "paper":    {"center": (x, y), "radius": r},
       "scissors": {"center": (x, y), "radius": r},
   }
   ```
   Buttons are modeled as **circles**, not boxes. If the new game's
   buttons are rectangular/irregular, `Humanizer._landing_point` and
   `_clamp_to_button` in `humanizer.py` need rewriting (currently pure
   polar/circular sampling) — this is the one piece of logic, not just
   config, that's shape-specific.

6. **Verify click registration** before trusting anything: single
   scripted click via `SystemCursor().move_to(...)` + `pyautogui.click(...)`
   at one button's center, then confirm visually (or via screenshot) that
   the game reacted. Do this per button if measurements are uncertain.

7. **Set the game's click cooldown**: `config.ANIMATION_COOLDOWN_SECONDS`
   is a **hard floor** added to every inter-click delay — the minimum
   time the game needs after a click before it'll accept the next one
   (result animation, state transition, etc.). This is a functional
   requirement, not a style knob; get it wrong and clicks queue up
   mid-animation or land in a non-interactive state. Determine it by
   asking the user or by testing (click, then reduce the wait until
   clicks start failing/misfiring, add margin). Current reference value:
   `5.0` seconds.

8. **Smoke test**: `python3 main.py --minutes 2`. Watch cursor behavior,
   then inspect `logs/session_*.csv` — confirm all three buttons get
   exercised and event sequences look sane (see schema below).

9. **Full run**: `caffeinate -d -i python3 main.py` (macOS — prevents
   display sleep/lock; a lock screen mid-session silently eats every
   click after it triggers, with no exception raised). Linux: disable
   screensaver/suspend equivalently. Windows: no direct equivalent
   implemented here — would need a keep-awake workaround before an
   unattended multi-hour run.

## config.py reference

**Device/game-specific — must verify or change per machine:**
- `BUTTONS[name]["center"]`, `BUTTONS[name]["radius"]` — per-button screen coords + px radius, circular hit area assumed.
- `SCREEN_MIN`, `SCREEN_MAX` — screen resolution bounds (top-left, bottom-right).
- `ANIMATION_COOLDOWN_SECONDS` — hard minimum post-click delay dictated by the game itself, not a behavioral choice.

**Behavioral tuning — safe to leave as-is or adjust to taste:**
- `SPEED` — divides humancursor's own `random.uniform(0.5, 2.0)` sampled move duration. Higher = faster travel. Does not touch curve shape (knots/offsets/distortion are generated inside `humancursor.SystemCursor.move_to` itself and are never overridden here) — this is the load-bearing property that lets speed scale up without the motion looking robotic. `SPEED=1.0` reproduces stock humancursor timing.
- `SESSION_HOURS` — total run length; `--minutes` CLI flag overrides it for smoke tests without touching this file.
- `DELAY_JITTER_MU` / `DELAY_JITTER_SIGMA` — lognormal human-reaction jitter layered on top of `ANIMATION_COOLDOWN_SECONDS`. Total delay = cooldown + jitter × fatigue multiplier, always ≥ cooldown by construction (lognormal draws are ≥ 0, so there's no clipping-at-a-wall artifact).
- `DELAY_MAX` — hard cap on cooldown + jitter combined.
- `FATIGUE_MAX_MULTIPLIER` / `FATIGUE_JITTER` — the jitter portion (not the cooldown) scales up linearly to this multiplier over the session, plus gaussian noise so the ramp isn't perfectly linear.
- `IDLE_DRIFT_PROB` / `IDLE_DRIFT_RADIUS` — small cursor movement between rounds instead of a parked cursor.
- `BREAK_PROB` / `BREAK_MIN_SECONDS` / `BREAK_MAX_SECONDS` — rare multi-minute pauses.
- `OVERSHOOT_PROB` / `OVERSHOOT_MAX_PX` — cursor overshoots the target then self-corrects.
- `MISCLICK_PROB` — clicks the wrong button, then recovers onto the intended one.
- `DOUBLE_CLICK_PROB` — accidental double-click on the intended button.
- `CLICK_CENTER_BIAS` — exponent on `random()` for polar radius sampling inside a button's circle; 0.5 ≈ uniform-by-area, 1.0 ≈ linear falloff toward center, >1.5 ≈ tight cluster near center.
- `CLICK_MAX_RADIUS_FRACTION` — caps sampled radius as a fraction of the button's true radius, so clicks never land at/past the true edge; kept conservative to absorb error in the measured radius.
- `SAME_BUTTON_STAY_PROB` / `STAY_JITTER_PX` — on a same-button repeat (from a choice streak), probability the cursor just micro-jitters in place (≤ `STAY_JITTER_PX`, no deliberate travel) instead of re-traveling to a fresh point on the button; the remainder still travels normally even on a repeat. See `Humanizer.click_button`.
- `CHOICE_BASE_WEIGHTS` — non-uniform rock/paper/scissors pick weights.
- `STREAK_CONTINUE_PROB` / `STREAK_MAX_LEN` — probability of repeating the previous choice each round (streakiness), capped at a max consecutive run before a forced reroll. Note: a forced reroll can still land on the same choice by chance, extending an observed run beyond `STREAK_MAX_LEN` — expected, not a bug.
- `LOG_DIR` — CSV output directory.

## CSV log schema

`logs/session_<timestamp>.csv`, columns: `timestamp, event, choice, x, y, delay_s`

`event` values: `click`, `stay_adjust`, `overshoot`, `correction`,
`misclick`, `double_click`, `idle_drift`, `break`, `delay`,
`failsafe_abort`, `force_stop`, `session_end`.

## Gotchas

- Coordinates are absolute screen pixels via `pyautogui`, not DOM/page
  coordinates — see step 4 above.
- `pyautogui.FAILSAFE = True` is intentional (set in `main.py`) — do not
  remove it. Moving the cursor into a screen corner aborts the run; it's
  the emergency stop.
- `humancursor.SystemCursor.click_on()` is deliberately **not used** —
  it bakes in a fixed `sleep(random.uniform(0.17, 0.28))` after every
  click, which would fight this project's own delay model.
  `humanizer.py` drives `SystemCursor.move_to` + `pyautogui.click`
  directly instead, so `sample_delay()` is the only thing pacing clicks.
- `humancursor`'s own `move_to` samples travel duration independent of
  pixel distance (`random.uniform(0.5, 2.0)` regardless of how far the
  cursor travels) — `SPEED` divides that draw; don't try to make speed
  distance-dependent without touching `humancursor`'s own source.
