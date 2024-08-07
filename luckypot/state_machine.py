from __future__ import annotations

from enum import Enum
from typing import cast


__all__ = ["StateMachine", "StateOperations", "BasicState"]


class StateOperations(Enum):
    """Operations that can be performed on a state stack."""

    NOP = 0
    POP = 1
    PUSH = 2
    REPLACE = 3


class BasicState:
    def __init__(self) -> None:
        super().__init__()
        self.next_state: tuple[StateOperations, BasicState | None] = (StateOperations.NOP, self)

    def on_enter(self):
        """Called when the state enters the stack (push or replace)."""
        self.next_state = (StateOperations.NOP, None)

    def on_pause(self):
        """Called when the state is about to not be the current state but still in the stack (push)."""

    def on_resume(self):
        """Called when the state is again at the top of the stack (after another was pop'ed)."""
        self.next_state = (StateOperations.NOP, None)

    def on_exit(self):
        """Called when the state leaves the stack (pop or replace)."""

    # State operations

    def pop_state(self, *_):
        """Return to the previous state in the state stack."""
        self.next_state = (StateOperations.POP, None)

    def push_state(self, new: BasicState):
        """Add a state to the stack that will be switched to."""
        self.next_state = (StateOperations.PUSH, new)

    def replace_state(self, new: BasicState):
        """Replace the current state with another one. Equivalent of a theoretic pop then push."""
        self.next_state = (StateOperations.REPLACE, new)

    def push_state_callback(self, new: type[BasicState], *args):
        """Return a callback that instanciates the new state and sets it as the next when called."""
        return lambda *_: self.push_state(new(*args))

    def replace_state_callback(self, new: type[BasicState], *args, **kwargs):
        """Return a callback that instanciates the new state and when called replaces the then current state."""
        return lambda *_: self.replace_state(new(*args, **kwargs))


class StateMachine[S: BasicState]:
    """A simple state machine with a stack of state."""

    def __init__(self, initial_state: type[S]):
        self.stack: list[S] = []
        self.execute_state_transition(StateOperations.PUSH, initial_state())

    def on_state_enter(self, state: S):
        """Override this method to do something when a new state is pushed."""

    @property
    def running(self):
        """Whether the state machine is non-empty."""
        return len(self.stack) > 0

    @property
    def state(self) -> S | None:
        """The current state.

        To update it, either set the next_state attribute of the current state,
        so that it's updated at the next call of go_to_next_state, or call
        execute_state_transition directly.
        """

        if self.stack:
            return self.stack[-1]
        return None

    def execute_state_transition(self, op: StateOperations, new: S | None):
        match (op, new):
            case (StateOperations.NOP, None):
                pass
            case (StateOperations.POP, None):
                if self.stack:
                    prev = self.stack.pop()
                    prev.on_exit()
                if self.stack:
                    self.stack[-1].on_resume()
            case (op, None):
                raise ValueError(f"A new state must be provided for {op}.")
            case (StateOperations.REPLACE, new):
                if self.stack:
                    prev = self.stack.pop()
                    prev.on_exit()
                self.stack.append(new)
                self.on_state_enter(new)
                new.on_enter()
            case (StateOperations.PUSH, new):
                if self.stack:
                    self.stack[-1].on_pause()
                self.stack.append(new)
                self.on_state_enter(new)
                new.on_enter()
            case _:
                print(type(op).__module__, StateOperations.__module__)
                print(type(op) is StateOperations)
                print(op, new)
                raise ValueError("Unknown operation type.")

    def go_to_next_state(self):
        assert self.state is not None
        op, new = self.state.next_state

        # It isn't necessarily, given the type of the tuple
        # But we assume people will use the API only with subclasses of S
        new = cast(S | None, new)

        self.execute_state_transition(op, new)
