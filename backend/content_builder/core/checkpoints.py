"""Atomic per-stage checkpoints, with output verification and a process lock."""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .artifacts import atomic_write_json, file_digest, fingerprint


@contextmanager
def build_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        locked = False
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
            yield
        finally:
            if locked:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)


class CheckpointStore:
    def __init__(self, root: Path):
        self.root = root

    def invalidate(self, name: str) -> None:
        path = self.root / f"{name}.json"
        if path.is_file():
            state = json.loads(path.read_text(encoding="utf-8"))
            state["status"] = "invalid"
            atomic_write_json(path, state)

    def run(self, name: str, inputs, action, *, force: bool = False, outputs=None):
        path = self.root / f"{name}.json"
        signature = fingerprint(inputs)
        if path.is_file() and not force:
            try:
                old = json.loads(path.read_text(encoding="utf-8"))
                if old.get("status") == "complete" and old.get("input_fingerprint") == signature and all(
                    Path(item["path"]).is_file() and file_digest(Path(item["path"])) == item["sha256"] for item in old.get("outputs", [])
                ):
                    print(f"[reuse] {name}")
                    return old["result"]
            except (OSError, ValueError, KeyError, TypeError):
                pass
        state = {"stage": name, "input_fingerprint": signature, "status": "running", "started_at": datetime.now(timezone.utc).isoformat()}
        atomic_write_json(path.with_suffix(".run.json"), state)
        print(f"[run] {name}")
        try:
            result = action()
            files = list(dict.fromkeys(outputs(result))) if outputs else []
            state.update(status="complete", result=result, outputs=[{"path": str(file.resolve()), "sha256": file_digest(file)} for file in files])
            atomic_write_json(path, state)
            atomic_write_json(path.with_suffix(".run.json"), {key: value for key, value in state.items() if key != "result"})
            return result
        except Exception as exc:
            state.update(status="failed", error_type=type(exc).__name__)
            atomic_write_json(path.with_suffix(".run.json"), state)
            raise
