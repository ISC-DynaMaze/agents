import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional


class ButtonEvent(Enum):
    PRESS = auto()
    RELEASE = auto()
    CLICK = auto()
    LONG_CLICK = auto()
    DOUBLE_CLICK = auto()


Handler = Callable[[str, ButtonEvent], None]


@dataclass
class _ButtonState:
    is_pressed: bool
    pressed_at: float
    last_click_at: Optional[float] = field(default=None)


@dataclass(frozen=True)
class ButtonConfig:
    long_click_threshold: float = 0.5
    double_click_window: float = 0.3


class ButtonHelper:
    def __init__(self, config: ButtonConfig = ButtonConfig()) -> None:
        self._config = config
        self._states: dict[str, _ButtonState] = {}
        self._handlers: list[tuple[frozenset[ButtonEvent], Handler]] = []

    def on(self, *events: ButtonEvent) -> Callable[[Handler], Handler]:
        event_set = frozenset(events)

        def decorator(fn: Handler) -> Handler:
            self._handlers.append((event_set, fn))
            return fn

        return decorator

    def add_handler(self, handler: Handler, *events: ButtonEvent) -> None:
        self._handlers.append((frozenset(events), handler))

    def update(self, button_id: str, pressed: bool):
        now: float = time.monotonic()
        if button_id not in self._states:
            self._states[button_id] = _ButtonState(
                is_pressed=not pressed, pressed_at=now
            )

        state = self._states[button_id]

        if pressed and not state.is_pressed:
            self._handle_press(button_id, state, now)
        elif not pressed and state.is_pressed:
            self._handle_release(button_id, state, now)

    def _handle_press(self, button_id: str, state: _ButtonState, now: float):
        state.is_pressed = True
        state.pressed_at = now
        self._emit(button_id, ButtonEvent.PRESS)

    def _handle_release(self, button_id: str, state: _ButtonState, now: float):
        held_for: float = now - state.pressed_at

        if held_for >= self._config.long_click_threshold:
            self._emit(button_id, ButtonEvent.LONG_CLICK)
            state.last_click_at = None
        elif (
            state.last_click_at is not None
            and now - state.last_click_at < self._config.double_click_window
        ):
            self._emit(button_id, ButtonEvent.DOUBLE_CLICK)
            state.last_click_at = None
        else:
            self._emit(button_id, ButtonEvent.CLICK)
            state.last_click_at = now

        state.is_pressed = False
        state.pressed_at = now
        self._emit(button_id, ButtonEvent.RELEASE)

    def _emit(self, button_id: str, event: ButtonEvent):
        for events, handler in self._handlers:
            if event in events:
                handler(button_id, event)
