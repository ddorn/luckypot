import json
from pathlib import Path

from .constants import ENTRY_POINT_DIR

__all__ = ["Settings", "settings"]


class Settings:
    """
    A singleton for all the settings that can be saved and loaded from the disk.

    Every attribute that is set in the __init__ will be saved and restored with :load: and :save:.
    """

    _instance = None
    PATH = ENTRY_POINT_DIR / "settings.json"

    def __new__(cls):
        if cls._instance:
            return cls._instance

        # create the only instance of cls
        self = super(Settings, cls).__new__(cls)
        cls._instance = self
        # Then we set the defaults and load it from the disk
        cls.__init__(self)
        self.load()
        # Finaly we swap __init__ and reset, so it will not be reset
        # Every time Settings() is called, as __init__ is always called after __new__.
        cls.reset = cls.__init__
        cls.__init__ = lambda self: None

        return self

    def __init__(self):
        self.debug = False
        self.mute = False

    def load(self):
        """(re)load the settings from the file. Called automatically on the first instance of Settings."""

        if self.PATH.exists():
            self.__dict__.update(json.loads(self.PATH.read_text()))

    def save(self):
        """Save the settings to its file. This is not called automatically."""

        self.PATH.write_text(json.dumps(self.__dict__))

    def reset(self):
        """Reset the settings."""

        # There is nothing here as this method is swapped with __init__
        # after the first instance. You don't like black magic ???


settings = Settings()
