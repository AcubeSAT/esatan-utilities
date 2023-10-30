import sys
from pathlib import Path

_PATHS = {"config": "src/config.toml"}


def get_path(name: str, relative: bool) -> Path:
    # https://www.pyinstaller.org/en/stable/CHANGES.html?highlight=_internal#incompatible-changes
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
        resource_path = base_path / _PATHS[name]
    else:
        script_dir = Path(__file__).parent
        resource_path = script_dir / _PATHS[name] if relative else Path(
            _PATHS[name]
        ).resolve()
    return resource_path
