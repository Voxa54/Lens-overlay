from __future__ import annotations

import ctypes

from . import win32
from .models import LensShape, Rect, Size


class OverlayError(RuntimeError):
    pass


class OverlayWindow:
    _class_name = "LensOverlayHostWindow"
    _class_registered = False
    _wndproc_ref = None

    def __init__(self) -> None:
        self.host_hwnd = None
        self.mag_hwnd = None
        self.visible = False
        self._last_shape = None
        self._last_size = None
        self._last_bounds = None

    def create(self, initial_size: Size, shape: LensShape) -> None:
        self._ensure_class()
        if not win32.mag.MagInitialize():
            raise OverlayError(f"Не удалось выполнить MagInitialize: {win32.get_last_error()}")

        instance = win32.kernel32.GetModuleHandleW(None)
        self.host_hwnd = win32.user32.CreateWindowExW(
            win32.WS_EX_TOPMOST
            | win32.WS_EX_LAYERED
            | win32.WS_EX_TRANSPARENT
            | win32.WS_EX_TOOLWINDOW
            | win32.WS_EX_NOACTIVATE,
            self._class_name,
            "Лупа",
            win32.WS_POPUP | win32.WS_CLIPCHILDREN,
            0,
            0,
            initial_size.width,
            initial_size.height,
            None,
            None,
            instance,
            None,
        )
        if not self.host_hwnd:
            raise OverlayError(f"Не удалось создать окно хоста через CreateWindowExW: {win32.get_last_error()}")

        self.mag_hwnd = win32.user32.CreateWindowExW(
            0,
            win32.WC_MAGNIFIER,
            "Лупа",
            win32.WS_CHILD | win32.WS_VISIBLE,
            0,
            0,
            initial_size.width,
            initial_size.height,
            self.host_hwnd,
            None,
            instance,
            None,
        )
        if not self.mag_hwnd:
            raise OverlayError(f"Не удалось создать окно Magnifier через CreateWindowExW: {win32.get_last_error()}")

        if not win32.user32.SetLayeredWindowAttributes(self.host_hwnd, 0, 255, win32.LWA_ALPHA):
            raise OverlayError(f"Не удалось вызвать SetLayeredWindowAttributes: {win32.get_last_error()}")

        host_array = (ctypes.c_void_p * 1)(int(self.host_hwnd))
        hwnd_list = ctypes.cast(host_array, ctypes.POINTER(ctypes.c_void_p))
        if not win32.mag.MagSetWindowFilterList(self.mag_hwnd, win32.MW_FILTERMODE_EXCLUDE, 1, hwnd_list):
            raise OverlayError(f"Не удалось вызвать MagSetWindowFilterList: {win32.get_last_error()}")

        self.apply_shape(shape, initial_size)
        self.hide()

    @classmethod
    def _ensure_class(cls) -> None:
        if cls._class_registered:
            return

        def wndproc(hwnd, message, w_param, l_param):
            if message == win32.WM_CLOSE:
                win32.user32.DestroyWindow(hwnd)
                return 0
            if message == win32.WM_DESTROY:
                win32.user32.PostQuitMessage(0)
                return 0
            return win32.user32.DefWindowProcW(hwnd, message, w_param, l_param)

        cls._wndproc_ref = win32.WNDPROC(wndproc)
        window_class = win32.WNDCLASSEXW()
        window_class.cbSize = ctypes.sizeof(win32.WNDCLASSEXW)
        window_class.style = 0
        window_class.lpfnWndProc = cls._wndproc_ref
        window_class.cbClsExtra = 0
        window_class.cbWndExtra = 0
        window_class.hInstance = win32.kernel32.GetModuleHandleW(None)
        window_class.hIcon = None
        window_class.hCursor = None
        window_class.hbrBackground = None
        window_class.lpszMenuName = None
        window_class.lpszClassName = cls._class_name
        window_class.hIconSm = None
        atom = win32.user32.RegisterClassExW(ctypes.byref(window_class))
        if not atom:
            raise OverlayError(f"Не удалось зарегистрировать класс окна через RegisterClassExW: {win32.get_last_error()}")
        cls._class_registered = True

    def apply_shape(self, shape: LensShape, size: Size) -> None:
        if self._last_shape == shape and self._last_size == size:
            return

        if shape == LensShape.ELLIPSE:
            region = win32.gdi32.CreateEllipticRgn(0, 0, size.width, size.height)
        else:
            region = win32.gdi32.CreateRectRgn(0, 0, size.width, size.height)

        if not region:
            raise OverlayError(f"Не удалось создать регион окна: {win32.get_last_error()}")
        if not win32.user32.SetWindowRgn(self.host_hwnd, region, True):
            raise OverlayError(f"Не удалось вызвать SetWindowRgn: {win32.get_last_error()}")

        self._last_shape = shape
        self._last_size = size

    def update_bounds(self, rect: Rect) -> None:
        if self._last_bounds == rect:
            return

        if not win32.user32.SetWindowPos(
            self.host_hwnd,
            win32.HWND_TOPMOST,
            rect.left,
            rect.top,
            rect.width,
            rect.height,
            win32.SWP_NOACTIVATE,
        ):
            raise OverlayError(f"Не удалось вызвать SetWindowPos: {win32.get_last_error()}")
        if not win32.user32.MoveWindow(self.mag_hwnd, 0, 0, rect.width, rect.height, True):
            raise OverlayError(f"Не удалось вызвать MoveWindow: {win32.get_last_error()}")

        self._last_bounds = rect

    def set_zoom(self, zoom: float) -> None:
        transform = win32.MAGTRANSFORM()
        transform.v[0][0] = zoom
        transform.v[0][1] = 0.0
        transform.v[0][2] = 0.0
        transform.v[1][0] = 0.0
        transform.v[1][1] = zoom
        transform.v[1][2] = 0.0
        transform.v[2][0] = 0.0
        transform.v[2][1] = 0.0
        transform.v[2][2] = 1.0
        if not win32.mag.MagSetWindowTransform(self.mag_hwnd, ctypes.byref(transform)):
            raise OverlayError(f"Не удалось вызвать MagSetWindowTransform: {win32.get_last_error()}")

    def set_source(self, rect: Rect) -> None:
        source = win32.RECT(rect.left, rect.top, rect.right, rect.bottom)
        if not win32.mag.MagSetWindowSource(self.mag_hwnd, source):
            raise OverlayError(f"Не удалось вызвать MagSetWindowSource: {win32.get_last_error()}")

    def show(self) -> None:
        if self.visible:
            return
        win32.user32.ShowWindow(self.host_hwnd, win32.SW_SHOW)
        win32.user32.UpdateWindow(self.host_hwnd)
        self.visible = True

    def hide(self) -> None:
        if self.host_hwnd:
            win32.user32.ShowWindow(self.host_hwnd, win32.SW_HIDE)
        self.visible = False

    def destroy(self) -> None:
        if self.host_hwnd:
            win32.user32.DestroyWindow(self.host_hwnd)
            self.host_hwnd = None
        win32.mag.MagUninitialize()
