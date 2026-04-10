from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .models import ActivationMode, LensShape, Point, Size


@dataclass
class KeyBindings:
    activation_key: str = "left_alt"
    move_modifier: str = "control"
    drag_modifier: str = "control"
    drag_button: str = "middle_mouse"
    exit_key: str = "end"


@dataclass
class LensConfig:
    zoom_presets: list[float]
    current_zoom_index: int
    size: Size
    min_size_px: int
    max_size_px: int
    size_step_px: int
    position: Point
    move_step_px: int = 6
    activation_mode: ActivationMode = ActivationMode.HOLD
    shape: LensShape = LensShape.RECTANGLE
    visible_on_start: bool = False
    refresh_hz: int = 0

    @property
    def zoom(self) -> float:
        return self.zoom_presets[self.current_zoom_index]

@dataclass
class AppConfig:
    lens: LensConfig
    keys: KeyBindings = field(default_factory=KeyBindings)


def _size_from_dict(data: dict) -> Size:
    side = max(1, min(int(data["width"]), int(data["height"])))
    return Size(width=side, height=side)


def _point_from_dict(data: dict) -> Point:
    return Point(x=int(data["x"]), y=int(data["y"]))


def build_default_config(screen_width: int, screen_height: int) -> AppConfig:
    min_side = min(screen_width, screen_height)
    quarter_side = max(320, min_side // 4)
    half_side = max(480, min_side // 2)
    custom_side = max(420, min_side // 3)
    quarter = Size(width=quarter_side, height=quarter_side)
    half = Size(width=half_side, height=half_side)
    custom = Size(width=custom_side, height=custom_side)

    return AppConfig(
        lens=LensConfig(
            zoom_presets=[2.0, 3.0, 5.0],
            current_zoom_index=0,
            size=quarter,
            min_size_px=120,
            max_size_px=max(quarter_side, min_side),
            size_step_px=1,
            position=Point(
                x=max(0, (screen_width - quarter.width) // 2),
                y=max(0, (screen_height - quarter.height) // 2),
            ),
        )
    )


def _config_from_dict(data: dict, screen_width: int, screen_height: int) -> AppConfig:
    defaults = build_default_config(screen_width, screen_height)
    lens_data = data.get("lens", {})
    key_data = data.get("keys", {})

    zoom_presets = lens_data.get("zoom_presets") or defaults.lens.zoom_presets
    legacy_size_presets = lens_data.get("size_presets")
    if "size" in lens_data:
        size = _size_from_dict(lens_data["size"])
    elif legacy_size_presets:
        legacy_index = min(
            max(int(lens_data.get("current_size_index", 0)), 0),
            len(legacy_size_presets) - 1,
        )
        size = _size_from_dict(legacy_size_presets[legacy_index])
    else:
        size = defaults.lens.size

    lens = LensConfig(
        zoom_presets=[float(value) for value in zoom_presets],
        current_zoom_index=min(
            max(int(lens_data.get("current_zoom_index", defaults.lens.current_zoom_index)), 0),
            len(zoom_presets) - 1,
        ),
        size=size,
        min_size_px=max(32, int(lens_data.get("min_size_px", defaults.lens.min_size_px))),
        max_size_px=max(64, int(lens_data.get("max_size_px", defaults.lens.max_size_px))),
        size_step_px=max(1, int(lens_data.get("size_step_px", defaults.lens.size_step_px))),
        position=_point_from_dict(lens_data.get("position", asdict(defaults.lens.position))),
        move_step_px=max(1, int(lens_data.get("move_step_px", defaults.lens.move_step_px))),
        activation_mode=ActivationMode(lens_data.get("activation_mode", defaults.lens.activation_mode.value)),
        shape=LensShape(lens_data.get("shape", defaults.lens.shape.value)),
        visible_on_start=bool(lens_data.get("visible_on_start", defaults.lens.visible_on_start)),
        refresh_hz=max(0, int(lens_data.get("refresh_hz", defaults.lens.refresh_hz))),
    )
    lens.max_size_px = max(lens.min_size_px, lens.max_size_px)
    current_side = min(max(lens.size.width, lens.min_size_px), lens.max_size_px)
    lens.size = Size(width=current_side, height=current_side)

    keys = KeyBindings(
        activation_key=str(key_data.get("activation_key", defaults.keys.activation_key)),
        move_modifier=str(key_data.get("move_modifier", defaults.keys.move_modifier)),
        drag_modifier=str(key_data.get("drag_modifier", defaults.keys.drag_modifier)),
        drag_button=str(key_data.get("drag_button", defaults.keys.drag_button)),
        exit_key=str(key_data.get("exit_key", defaults.keys.exit_key)),
    )
    return AppConfig(lens=lens, keys=keys)


def config_to_dict(config: AppConfig) -> dict:
    return {
        "lens": {
            "zoom_presets": config.lens.zoom_presets,
            "current_zoom_index": config.lens.current_zoom_index,
            "size": asdict(config.lens.size),
            "min_size_px": config.lens.min_size_px,
            "max_size_px": config.lens.max_size_px,
            "size_step_px": config.lens.size_step_px,
            "position": asdict(config.lens.position),
            "move_step_px": config.lens.move_step_px,
            "activation_mode": config.lens.activation_mode.value,
            "shape": config.lens.shape.value,
            "visible_on_start": config.lens.visible_on_start,
            "refresh_hz": config.lens.refresh_hz,
        },
        "keys": asdict(config.keys),
    }


class ConfigStore:
    def __init__(self, path: Path, screen_width: int, screen_height: int) -> None:
        self.path = path
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = self._load()
        self._dirty = False

    def _load(self) -> AppConfig:
        if not self.path.exists():
            config = build_default_config(self.screen_width, self.screen_height)
            self.path.write_text(json.dumps(config_to_dict(config), indent=2), encoding="utf-8")
            return config

        data = json.loads(self.path.read_text(encoding="utf-8"))
        return _config_from_dict(data, self.screen_width, self.screen_height)

    def mark_dirty(self) -> None:
        self._dirty = True

    def flush(self) -> None:
        if not self._dirty:
            return

        self.path.write_text(json.dumps(config_to_dict(self.config), indent=2), encoding="utf-8")
        self._dirty = False
