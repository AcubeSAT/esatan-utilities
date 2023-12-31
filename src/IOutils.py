from pathlib import Path
from tomllib import load

from config_model import Config
from eltypes import config, config_model


def _read_toml(filename: Path) -> config:
    with open(filename, mode="rb") as fp:
        config = load(fp)
    return config


def read_config(filename: Path) -> config_model:
    conf = _read_toml(filename)
    return Config.model_validate(conf)
