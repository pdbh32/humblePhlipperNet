from __future__ import annotations

import pathlib

import portalocker

from humblePhlipperPython.config.paths import EVENTS_DIR
from humblePhlipperPython.schemata.domain.event import Event
from humblePhlipperPython.utils.file_helpers import sanitise_filename, lock

def get_session_dir(session_timestamp: float) -> pathlib.Path:
    return EVENTS_DIR / f"ts={int(session_timestamp)}" 

def get_user_path(user: str, session_timestamp: float) -> pathlib.Path:
    return get_session_dir(session_timestamp) / f"name={sanitise_filename(user)}.jsonl"

def save(user: str, session_timestamp: float, events: list[Event]) -> None:
    path = get_user_path(user, session_timestamp)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock(lock_path, "a", portalocker.LockFlags.EXCLUSIVE):
        with open(path, "a", encoding="utf-8") as handle:
            for event in events:
                if event is None:
                    continue
                handle.write(event.model_dump_json() + "\n")

def load(user: str, session_timestamp: float) -> list[Event]:
    path = get_user_path(user, session_timestamp)
    lock_path = path.with_suffix(path.suffix + ".lock")
    if not path.exists():
        return []
    with lock(lock_path, "a", portalocker.LockFlags.SHARED):
        with open(path, "r", encoding="utf-8") as handle:
            return [Event.model_validate_json(line) for line in handle if line.strip()]
        
def  load_all(session_timestamp: float) -> dict[str, list[Event]]:
    return {
        (user := path.stem.split("=", 1)[1]): load(user, session_timestamp)
        for path in get_session_dir(session_timestamp).glob("name=*.jsonl")
    } 