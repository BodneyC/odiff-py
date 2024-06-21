import os
import json

import yaml

GIT_ROOT_DIR: str = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), ".."
)

TRUNC_MAX = 100
TABULATION_VALUE_MAX = 40


def trunc(s: str, n: int = TRUNC_MAX) -> str:
    return (s[:n] + "...") if len(s) > n else s


def get_aux_file(fname: str) -> str:
    with open(f"{GIT_ROOT_DIR}/aux/{fname}") as f:
        return f.read()


def get_aux_json(fname: str) -> dict:
    with open(f"{GIT_ROOT_DIR}/aux/{fname}") as f:
        return json.load(f)


def get_aux_yaml(fname: str) -> dict:
    with open(f"{GIT_ROOT_DIR}/aux/{fname}") as f:
        return yaml.load(f, Loader=yaml.SafeLoader)
