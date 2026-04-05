import os


def get_env(*names: str, default=None):
    for name in names:
        value = os.getenv(name)
        if value is None:
            continue
        stripped = value.strip()
        if stripped == "":
            continue
        return stripped
    return default


def get_env_int(*names: str, default: int) -> int:
    value = get_env(*names, default=None)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_env_float(*names: str, default: float) -> float:
    value = get_env(*names, default=None)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_env_bool(*names: str, default: bool) -> bool:
    value = get_env(*names, default=None)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}
