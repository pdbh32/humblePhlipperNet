from __future__ import annotations

import contextlib
import pathlib
import re
from typing import Iterator, TextIO

import portalocker

def sanitise_filename(string: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", string).strip().rstrip(".")

@contextlib.contextmanager
def lock(path: pathlib.Path, mode: str, lock_type: portalocker.LockFlags) -> Iterator[TextIO]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with portalocker.Lock(path, mode, flags=lock_type) as handle:
        yield handle