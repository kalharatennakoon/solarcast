"""
In-memory cache of the trained model.

The model is read from disk once and reused for every request. It is reloaded
only when the model file changes (after POST /train, or a CLI retrain), which
is detected by comparing the file's modification time.
"""

import logging
import threading

from api.metrics import MODEL_LOADED, MODEL_TRAINED_TIMESTAMP
from model.artefacts import load_artefacts, model_exists, model_path

logger = logging.getLogger("solarcast.model_store")


class ModelStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._artefacts: tuple | None = None
        self._version: int | None = None
        self.load_error: str | None = None

    def get(self) -> tuple | None:
        """Return (model, ratios), or None if no usable model is available."""
        try:
            version = model_path().stat().st_mtime_ns if model_exists() else None
        except FileNotFoundError:
            version = None

        with self._lock:
            if version != self._version:
                self._load(version)
            return self._artefacts

    def _load(self, version: int | None) -> None:
        self._artefacts = None
        self.load_error = None
        if version is not None:
            try:
                self._artefacts = load_artefacts()
                logger.info("Loaded model from %s", model_path())
            except Exception as exc:
                # e.g. a model saved by an incompatible library version.
                # Report "not trained" so the fix is simply to retrain.
                self.load_error = f"{type(exc).__name__}: {exc}"
                logger.exception("Could not load model from %s", model_path())

        # Remember the version even on failure, so a broken file is not
        # re-read on every request — only when it changes.
        self._version = version
        MODEL_LOADED.set(1 if self._artefacts is not None else 0)
        MODEL_TRAINED_TIMESTAMP.set(version / 1e9 if self._artefacts is not None else 0)

    def reset(self) -> None:
        """Forget the cached model so the next get() reads from disk again."""
        with self._lock:
            self._artefacts = None
            self._version = None
            self.load_error = None


model_store = ModelStore()
