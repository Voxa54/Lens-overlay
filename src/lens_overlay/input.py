from __future__ import annotations

from dataclasses import dataclass

from . import win32
from .models import Point


KEY_MAP = {
    "left_alt": (win32.VK_LMENU,),
    "control": (win32.VK_CONTROL,),
    "shift": (win32.VK_SHIFT,),
    "left": (win32.VK_LEFT,),
    "right": (win32.VK_RIGHT,),
    "up": (win32.VK_UP,),
    "down": (win32.VK_DOWN,),
    "page_up": (win32.VK_PRIOR,),
    "page_down": (win32.VK_NEXT,),
    "end": (win32.VK_END,),
    "plus": (win32.VK_ADD, win32.VK_OEM_PLUS),
    "minus": (win32.VK_SUBTRACT, win32.VK_OEM_MINUS),
    "left_mouse": (win32.VK_LBUTTON,),
    "middle_mouse": (win32.VK_MBUTTON,),
}


def _is_down(name: str) -> bool:
    return any(win32.user32.GetAsyncKeyState(code) & 0x8000 for code in KEY_MAP[name])


@dataclass
class InputSnapshot:
    current: dict[str, bool]
    previous: dict[str, bool]
    cursor: Point
    previous_cursor: Point

    def down(self, name: str) -> bool:
        return self.current.get(name, False)

    def pressed(self, name: str) -> bool:
        return self.current.get(name, False) and not self.previous.get(name, False)

    def released(self, name: str) -> bool:
        return not self.current.get(name, False) and self.previous.get(name, False)


class InputManager:
    def __init__(self, watched_names: list[str]) -> None:
        self.watched_names = watched_names
        self._previous = {name: False for name in watched_names}
        self._previous_cursor = Point(0, 0)

    def poll(self) -> InputSnapshot:
        point = win32.POINT()
        win32.user32.GetCursorPos(point)
        current = {name: _is_down(name) for name in self.watched_names}
        snapshot = InputSnapshot(
            current=current,
            previous=self._previous.copy(),
            cursor=Point(point.x, point.y),
            previous_cursor=self._previous_cursor,
        )
        self._previous = current
        self._previous_cursor = snapshot.cursor
        return snapshot
