from __future__ import annotations

import time

from .config import ConfigStore
from .input import InputManager, InputSnapshot
from .models import ActivationMode, Point, Rect, Size
from .overlay import OverlayWindow


class LensController:
    def __init__(
        self,
        store: ConfigStore,
        overlay: OverlayWindow,
        input_manager: InputManager,
        virtual_screen: Rect,
    ) -> None:
        self.store = store
        self.config = store.config
        self.overlay = overlay
        self.input = input_manager
        self.virtual_screen = virtual_screen
        self.active = self.config.lens.visible_on_start
        self.position_x = float(self.config.lens.position.x)
        self.position_y = float(self.config.lens.position.y)
        self.dragging = False
        self.drag_origin_cursor = Point(0, 0)
        self.drag_origin_position = Point(self.config.lens.position.x, self.config.lens.position.y)
        self.keyboard_move_speed_px = max(60.0, float(self.config.lens.move_step_px) * 12.0)
        self.last_save_time = time.perf_counter()
        self.last_frame_time = time.perf_counter()
        self.last_change_time = self.last_frame_time
        self.save_debounce_seconds = 0.15
        self.last_resize_time = 0.0
        self.resize_repeat_seconds = 0.01

    def update(self) -> bool:
        now = time.perf_counter()
        delta_seconds = min(0.05, max(0.0, now - self.last_frame_time))
        self.last_frame_time = now
        snapshot = self.input.poll()
        self._handle_exit(snapshot)
        self._handle_activation(snapshot)
        self._handle_zoom(snapshot)
        self._handle_size(snapshot)
        self._handle_keyboard_move(snapshot, delta_seconds)
        self._handle_drag(snapshot)
        self._clamp_position()
        self._render()
        self._flush_config()
        return True

    def _handle_exit(self, snapshot: InputSnapshot) -> None:
        if snapshot.pressed(self.config.keys.exit_key) and snapshot.down("control") and snapshot.down("left_alt"):
            raise KeyboardInterrupt

    def _handle_activation(self, snapshot: InputSnapshot) -> None:
        activation_key = self.config.keys.activation_key
        if self.config.lens.activation_mode == ActivationMode.HOLD:
            self.active = snapshot.down(activation_key)
            return
        if snapshot.pressed(activation_key):
            self.active = not self.active

    def _handle_zoom(self, snapshot: InputSnapshot) -> None:
        if not (snapshot.down("control") and snapshot.down("left_alt")):
            return

        lens = self.config.lens
        if snapshot.pressed("plus") and lens.current_zoom_index < len(lens.zoom_presets) - 1:
            lens.current_zoom_index += 1
            self._mark_config_changed(immediate=True)
        elif snapshot.pressed("minus") and lens.current_zoom_index > 0:
            lens.current_zoom_index -= 1
            self._mark_config_changed(immediate=True)

    def _handle_size(self, snapshot: InputSnapshot) -> None:
        if not (snapshot.down("control") and snapshot.down("left_alt")):
            return

        lens = self.config.lens
        now = time.perf_counter()
        if now - self.last_resize_time < self.resize_repeat_seconds:
            return

        if snapshot.down("page_up"):
            new_side = min(lens.max_size_px, lens.size.width + lens.size_step_px)
            if new_side != lens.size.width:
                lens.size = Size(width=new_side, height=new_side)
                self.last_resize_time = now
                self._mark_config_changed()
        elif snapshot.down("page_down"):
            new_side = max(lens.min_size_px, lens.size.width - lens.size_step_px)
            if new_side != lens.size.width:
                lens.size = Size(width=new_side, height=new_side)
                self.last_resize_time = now
                self._mark_config_changed()

    def _handle_keyboard_move(self, snapshot: InputSnapshot, delta_seconds: float) -> None:
        if not self.active:
            return
        if not (snapshot.down(self.config.keys.move_modifier) and snapshot.down("left_alt")):
            return

        if delta_seconds <= 0.0:
            return

        distance = self.keyboard_move_speed_px * delta_seconds
        moved = False
        if snapshot.down("left"):
            self.position_x -= distance
            moved = True
        if snapshot.down("right"):
            self.position_x += distance
            moved = True
        if snapshot.down("up"):
            self.position_y -= distance
            moved = True
        if snapshot.down("down"):
            self.position_y += distance
            moved = True

        if moved:
            self._sync_config_position()
            self._mark_config_changed()

    def _handle_drag(self, snapshot: InputSnapshot) -> None:
        if not self.active:
            self.dragging = False
            return

        drag_requested = snapshot.down(self.config.keys.drag_button) and snapshot.down(self.config.keys.drag_modifier)
        if drag_requested and not self.dragging:
            self.dragging = True
            self.drag_origin_cursor = snapshot.cursor
            self.drag_origin_position = Point(self.config.lens.position.x, self.config.lens.position.y)
            return

        if not drag_requested:
            if self.dragging:
                self.dragging = False
                self._mark_config_changed(immediate=True)
            self.dragging = False
            return

        dx = snapshot.cursor.x - self.drag_origin_cursor.x
        dy = snapshot.cursor.y - self.drag_origin_cursor.y
        self.position_x = float(self.drag_origin_position.x + dx)
        self.position_y = float(self.drag_origin_position.y + dy)
        self._sync_config_position()
        self._mark_config_changed()

    def _clamp_position(self) -> None:
        size = self.config.lens.size
        min_x = self.virtual_screen.left
        min_y = self.virtual_screen.top
        max_x = max(min_x, self.virtual_screen.right - size.width)
        max_y = max(min_y, self.virtual_screen.bottom - size.height)
        clamped_x = min(max(self.position_x, min_x), float(max_x))
        clamped_y = min(max(self.position_y, min_y), float(max_y))
        if clamped_x != self.position_x or clamped_y != self.position_y:
            self.position_x = clamped_x
            self.position_y = clamped_y
            self._sync_config_position()
            self._mark_config_changed()
            return

        self._sync_config_position()

    def _render(self) -> None:
        if not self.active:
            self.overlay.hide()
            return

        size = self.config.lens.size
        position = self.config.lens.position
        bounds = Rect(
            left=position.x,
            top=position.y,
            right=position.x + size.width,
            bottom=position.y + size.height,
        )
        source = self._build_source_rect(bounds, size, self.config.lens.zoom)
        self.overlay.apply_shape(self.config.lens.shape, size)
        self.overlay.update_bounds(bounds)
        self.overlay.set_zoom(self.config.lens.zoom)
        self.overlay.set_source(source)
        self.overlay.show()

    def _build_source_rect(self, bounds: Rect, size: Size, zoom: float) -> Rect:
        source_width = max(1, int(size.width / zoom))
        source_height = max(1, int(size.height / zoom))
        center_x = bounds.left + size.width // 2
        center_y = bounds.top + size.height // 2
        left = center_x - source_width // 2
        top = center_y - source_height // 2
        max_left = max(self.virtual_screen.left, self.virtual_screen.right - source_width)
        max_top = max(self.virtual_screen.top, self.virtual_screen.bottom - source_height)
        left = min(max(left, self.virtual_screen.left), max_left)
        top = min(max(top, self.virtual_screen.top), max_top)
        return Rect(
            left=left,
            top=top,
            right=left + source_width,
            bottom=top + source_height,
        )

    def _flush_config(self) -> None:
        now = time.perf_counter()
        if not self.store._dirty:
            return
        if now - self.last_change_time < self.save_debounce_seconds:
            return
        self.store.flush()
        self.last_save_time = now

    def _sync_config_position(self) -> None:
        self.config.lens.position = Point(int(round(self.position_x)), int(round(self.position_y)))

    def _mark_config_changed(self, immediate: bool = False) -> None:
        self.store.mark_dirty()
        self.last_change_time = time.perf_counter()
        if immediate:
            self.store.flush()
            self.last_save_time = self.last_change_time
