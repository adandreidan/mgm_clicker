"""Soak-test loop: click rock/paper/scissors semi-randomly for SESSION_HOURS,
logging every action to a timestamped CSV for later replay against the
bot-detection logic. Ctrl+C shuts down gracefully; moving the mouse to a
screen corner triggers pyautogui's FAILSAFE and aborts immediately.
"""

import csv
import os
import random
import signal
import time
from datetime import datetime

import pyautogui

import config
from humanizer import Humanizer

pyautogui.FAILSAFE = True

_shutdown_requested = False


def _handle_sigint(signum, frame):
    global _shutdown_requested
    if _shutdown_requested:
        raise KeyboardInterrupt  # second Ctrl+C: stop waiting, exit now
    print("\n[!] Ctrl+C received, finishing current round then shutting down...")
    _shutdown_requested = True


signal.signal(signal.SIGINT, _handle_sigint)


class CsvLogger:
    def __init__(self, path):
        self._file = open(path, "w", newline="")
        self._writer = csv.writer(self._file)
        self._writer.writerow(["timestamp", "event", "choice", "x", "y", "delay_s"])

    def log(self, event, choice="", x="", y="", delay_s=""):
        self._writer.writerow([
            datetime.now().isoformat(timespec="milliseconds"),
            event, choice, x, y, delay_s,
        ])
        self._file.flush()

    def close(self):
        self._file.close()


def main():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    log_path = os.path.join(config.LOG_DIR, f"session_{datetime.now():%Y%m%d_%H%M%S}.csv")
    logger = CsvLogger(log_path)
    print(f"Logging to {log_path}")
    print(f"Session length: {config.SESSION_HOURS}h, SPEED={config.SPEED}. Ctrl+C to stop early.")

    humanizer = Humanizer()
    deadline = time.monotonic() + config.SESSION_HOURS * 3600
    rounds = 0

    try:
        while not _shutdown_requested and time.monotonic() < deadline:
            break_len = humanizer.maybe_take_break()
            if break_len is not None:
                logger.log("break", delay_s=round(break_len, 2))
                continue

            drift_target = humanizer.idle_drift()
            if drift_target is not None:
                logger.log("idle_drift", x=drift_target[0], y=drift_target[1])

            choice = humanizer.choose()
            for ev in humanizer.click_button(choice):
                logger.log(
                    ev["event"],
                    choice=ev.get("choice", ""),
                    x=ev.get("x", ""),
                    y=ev.get("y", ""),
                )
            rounds += 1

            delay = humanizer.sample_delay()
            logger.log("delay", choice=choice, delay_s=round(delay, 3))
            time.sleep(delay)

    except pyautogui.FailSafeException:
        print("\n[!] FAILSAFE triggered (cursor hit a screen corner). Stopping.")
        logger.log("failsafe_abort")
    except KeyboardInterrupt:
        print("\n[!] Force-stopped.")
        logger.log("force_stop")
    finally:
        logger.log("session_end")
        logger.close()
        print(f"Done. {rounds} rounds played. Log: {log_path}")


if __name__ == "__main__":
    main()
