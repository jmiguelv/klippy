import json
import os

class StateStore:
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def get_last_sync(self, key: str) -> str | None:
        return self.state.get(key)

    def set_last_sync(self, key: str, timestamp: str):
        self.state[key] = timestamp
