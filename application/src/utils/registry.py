class Registry[Key, Value]:

    def __init__(self):
        self._store: dict[Key, Value] = {}

    def register(self, key: Key, value: Value):

        if key in self._store:
            raise ValueError(f"Key {key} already registered.")

        self._store[key] = value

    def create(self, key: Key, config: dict):
        if key not in self._store:
            raise KeyError(f"Key '{key}' not found in registry.")

        return self._store[key](config)




