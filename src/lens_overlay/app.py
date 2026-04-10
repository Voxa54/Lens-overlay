from __future__ import annotations

import time
from pathlib import Path

from . import win32
from .config import ConfigStore
from .controller import LensController
from .input import InputManager
from .models import Rect
from .overlay import OverlayError, OverlayWindow


def _get_virtual_screen() -> Rect:
    left = win32.user32.GetSystemMetrics(win32.SM_XVIRTUALSCREEN)
    top = win32.user32.GetSystemMetrics(win32.SM_YVIRTUALSCREEN)
    width = win32.user32.GetSystemMetrics(win32.SM_CXVIRTUALSCREEN)
    height = win32.user32.GetSystemMetrics(win32.SM_CYVIRTUALSCREEN)
    return Rect(left=left, top=top, right=left + width, bottom=top + height)


def _pump_messages() -> bool:
    message = win32.MSG()
    while win32.user32.PeekMessageW(message, None, 0, 0, win32.PM_REMOVE):
        if message.message == win32.WM_QUIT:
            return False
        win32.user32.TranslateMessage(message)
        win32.user32.DispatchMessageW(message)
    return True


def _describe_key(name: str) -> str:
    labels = {
        "left_alt": "Left Alt",
        "control": "Ctrl",
        "shift": "Shift",
        "page_up": "Page Up",
        "page_down": "Page Down",
        "middle_mouse": "средняя кнопка мыши",
        "end": "End",
    }
    return labels.get(name, name)


def _describe_activation_mode(mode: str) -> str:
    labels = {
        "hold": "удержание",
        "toggle": "переключение",
    }
    return labels.get(mode, mode)


def _print_usage(config_path: Path, store: ConfigStore) -> None:
    activation = _describe_key(store.config.keys.activation_key)
    mode = _describe_activation_mode(store.config.lens.activation_mode.value)
    print("Оверлей-лупа запущен.")
    print(f"Настройки: {config_path}")
    print(f"Активация: {activation} ({mode})")
    print("Как пользоваться:")
    print("  Left Alt: показать лупу")
    print("  Ctrl + Left Alt + стрелки: перемещать лупу")
    print("  Ctrl + Left Alt + Plus/Minus: менять масштаб")
    print("  Ctrl + Left Alt + Page Up/Page Down: менять размер лупы на 1 пиксель")
    print("  Ctrl + средняя кнопка мыши + движение: перетаскивать лупу")
    print("  Ctrl + Left Alt + End: выйти")


def main() -> int:
    virtual_screen = _get_virtual_screen()
    config_path = Path(__file__).resolve().parents[2] / "settings.json"
    store = ConfigStore(config_path, virtual_screen.width, virtual_screen.height)
    overlay = OverlayWindow()
    input_manager = InputManager(
        [
            "left_alt",
            "control",
            "shift",
            "left",
            "right",
            "up",
            "down",
            "page_up",
            "page_down",
            "plus",
            "minus",
            "middle_mouse",
            "end",
        ]
    )
    controller = LensController(store, overlay, input_manager, virtual_screen)
    winmm_started = False

    try:
        win32.winmm.timeBeginPeriod(1)
        winmm_started = True
        overlay.create(store.config.lens.size, store.config.lens.shape)
        _print_usage(config_path, store)
        if store.config.lens.refresh_hz > 0:
            print(f"Целевая частота обновления: {store.config.lens.refresh_hz} FPS.")
            frame_interval = 1.0 / store.config.lens.refresh_hz
        else:
            print("Целевая частота обновления: без ограничения.")
            frame_interval = 0.0

        next_tick = time.perf_counter()
        while _pump_messages():
            controller.update()
            if frame_interval <= 0.0:
                win32.kernel32.Sleep(0)
                continue

            next_tick += frame_interval
            remaining = next_tick - time.perf_counter()
            if remaining > 0.002:
                win32.kernel32.Sleep(max(0, int((remaining - 0.001) * 1000)))
            else:
                while time.perf_counter() < next_tick:
                    pass
    except KeyboardInterrupt:
        pass
    except OverlayError as exc:
        print(f"Не удалось инициализировать оверлей: {exc}")
        return 1
    finally:
        store.flush()
        overlay.destroy()
        if winmm_started:
            win32.winmm.timeEndPeriod(1)

    return 0
