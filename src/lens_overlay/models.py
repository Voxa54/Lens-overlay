from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActivationMode(str, Enum):
    HOLD = "hold"
    TOGGLE = "toggle"


class LensShape(str, Enum):
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Size:
    width: int
    height: int


@dataclass
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top
