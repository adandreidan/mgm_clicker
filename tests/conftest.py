import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# humanizer imports pyautogui/humancursor, which need a display and OS
# input permissions. Stub them so the pure logic can be tested headless.
sys.modules.setdefault("pyautogui", mock.MagicMock())
sys.modules.setdefault("humancursor", mock.MagicMock())
