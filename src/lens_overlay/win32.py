from __future__ import annotations

import ctypes
from ctypes import wintypes


user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
mag = ctypes.WinDLL("Magnification", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
winmm = ctypes.WinDLL("winmm", use_last_error=True)

BOOL = wintypes.BOOL
DWORD = wintypes.DWORD
UINT = wintypes.UINT
LONG = wintypes.LONG
FLOAT = ctypes.c_float
HANDLE = wintypes.HANDLE
HINSTANCE = wintypes.HMODULE
HICON = HANDLE
HCURSOR = HANDLE
HBRUSH = HANDLE
HRGN = HANDLE

if ctypes.sizeof(ctypes.c_void_p) == 8:
    LRESULT = ctypes.c_longlong
else:
    LRESULT = ctypes.c_long

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, UINT, wintypes.WPARAM, wintypes.LPARAM)

WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_CLIPCHILDREN = 0x02000000

WS_EX_TOPMOST = 0x00000008
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000

LWA_ALPHA = 0x00000002

SW_HIDE = 0
SW_SHOW = 5

PM_REMOVE = 0x0001

WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_QUIT = 0x0012

SWP_NOACTIVATE = 0x0010

VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_END = 0x23
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_LMENU = 0xA4
VK_LBUTTON = 0x01
VK_MBUTTON = 0x04
VK_ADD = 0x6B
VK_SUBTRACT = 0x6D
VK_OEM_PLUS = 0xBB
VK_OEM_MINUS = 0xBD

SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

MW_FILTERMODE_EXCLUDE = 0

WC_MAGNIFIER = "Magnifier"
HWND_TOPMOST = wintypes.HWND(-1)


class POINT(ctypes.Structure):
    _fields_ = [("x", LONG), ("y", LONG)]


class RECT(ctypes.Structure):
    _fields_ = [("left", LONG), ("top", LONG), ("right", LONG), ("bottom", LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", DWORD),
        ("pt", POINT),
    ]


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", UINT),
        ("style", UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", HICON),
    ]


class MAGTRANSFORM(ctypes.Structure):
    _fields_ = [("v", (FLOAT * 3) * 3)]


user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = [wintypes.HWND, UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.RegisterClassExW.restype = wintypes.ATOM
user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = [
    DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    HINSTANCE,
    wintypes.LPVOID,
]
user32.DestroyWindow.restype = BOOL
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.ShowWindow.restype = BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UpdateWindow.restype = BOOL
user32.UpdateWindow.argtypes = [wintypes.HWND]
user32.SetWindowPos.restype = BOOL
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    UINT,
]
user32.MoveWindow.restype = BOOL
user32.MoveWindow.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, BOOL]
user32.SetLayeredWindowAttributes.restype = BOOL
user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, DWORD, wintypes.BYTE, DWORD]
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PeekMessageW.restype = BOOL
user32.PeekMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, UINT, UINT, UINT]
user32.TranslateMessage.restype = BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.GetCursorPos.restype = BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.SetWindowRgn.restype = ctypes.c_int
user32.SetWindowRgn.argtypes = [wintypes.HWND, HRGN, BOOL]

gdi32.CreateRectRgn.restype = HRGN
gdi32.CreateRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
gdi32.CreateEllipticRgn.restype = HRGN
gdi32.CreateEllipticRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

kernel32.GetModuleHandleW.restype = HINSTANCE
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.Sleep.argtypes = [DWORD]

mag.MagInitialize.restype = BOOL
mag.MagUninitialize.restype = BOOL
mag.MagSetWindowSource.restype = BOOL
mag.MagSetWindowSource.argtypes = [wintypes.HWND, RECT]
mag.MagSetWindowTransform.restype = BOOL
mag.MagSetWindowTransform.argtypes = [wintypes.HWND, ctypes.POINTER(MAGTRANSFORM)]
mag.MagSetWindowFilterList.restype = BOOL
mag.MagSetWindowFilterList.argtypes = [wintypes.HWND, DWORD, ctypes.c_int, ctypes.POINTER(wintypes.HWND)]

dwmapi.DwmFlush.restype = ctypes.c_long
winmm.timeBeginPeriod.restype = UINT
winmm.timeBeginPeriod.argtypes = [UINT]
winmm.timeEndPeriod.restype = UINT
winmm.timeEndPeriod.argtypes = [UINT]


def get_last_error() -> int:
    return ctypes.get_last_error()
