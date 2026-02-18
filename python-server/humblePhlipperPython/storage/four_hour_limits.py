from __future__ import annotations

import os
import pathlib
import json

import portalocker

from humblePhlipperPython.utils.file_helpers import sanitise_filename, lock
from humblePhlipperPython.config.paths import FOUR_HOUR_LIMITS_DIR
from humblePhlipperPython.schemata.domain.four_hour_limit import FourHourLimit

def get_path(user: str) -> pathlib.Path:
    return FOUR_HOUR_LIMITS_DIR / f"{sanitise_filename(user)}.json"

def load(user: str) -> dict[int, FourHourLimit]:
    path = get_path(user)
    lock_path = path.with_suffix(path.suffix + ".lock")
    if not os.path.exists(path):
        return {}
    with lock(lock_path, "a", portalocker.LockFlags.SHARED):
        with open(path, "r", encoding="utf-8") as handle:
            return {int(k): FourHourLimit.model_validate(v) for k, v in (json.load(handle)).items()}

def save(user: str, map: dict[int, FourHourLimit]) -> None:
    path = get_path(user)
    lock_path = path.with_suffix(path.suffix + ".lock")
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with lock(lock_path, "a", portalocker.LockFlags.EXCLUSIVE):
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump({str(k): v.model_dump(by_alias=True) for k, v in map.items()}, handle, indent=4)
        tmp_path.replace(path)