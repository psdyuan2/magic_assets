"""Configure the local image2 settings used by magic-assets."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

SKILL_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = SKILL_ROOT / "ma_settings.json"
FIELDS = ("endpoint", "apikey", "model_name")
DEFAULT_MODEL = "gpt-image-2"


class SafeArgumentParser(argparse.ArgumentParser):
    """Parser that never echoes option values (an apikey may be one of them)."""

    def error(self, message: str) -> None:
        self.exit(2, "config error: invalid arguments (run 'run.py config --help')")


def normalized_field(name: str, value: str) -> str:
    value = str(value).strip()
    if name == "endpoint":
        value = value.rstrip("/")
    return value


def endpoint_error(value: str) -> str | None:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return "must be a valid URL"
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "must be an http:// or https:// URL with a host"
    return None


def display_endpoint(value: str) -> str:
    try:
        return urlsplit(value).hostname or urlsplit(value).netloc
    except ValueError:
        return "invalid"


def display_key(value: str) -> str:
    suffix = value[-4:] if len(value) >= 4 else ""
    return f"***{suffix} (length={len(value)})"


def read_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.exit(f"config error: cannot read {SETTINGS_PATH.name}: {error}")
    if not isinstance(data, dict):
        sys.exit(f"config error: {SETTINGS_PATH.name} must be a JSON object")
    return data


def write_settings(data: dict) -> None:
    SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    SETTINGS_PATH.chmod(0o600)


def validate_values(data: dict, *, fail_fast: bool) -> bool:
    problems: list[str] = []
    for name in FIELDS:
        value = normalized_field(name, str(data.get(name) or ""))
        if not value:
            problems.append(name)
        elif name == "endpoint" and endpoint_error(value):
            problems.append(f"{name} (invalid URL)")
    if problems:
        if fail_fast:
            sys.exit(f"config error: invalid {' '.join(problems)}")
        return False
    return True


def prompt_value(label: str, *, secret: bool = False, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        prompt = f"{label}{suffix}: "
        try:
            value = getpass.getpass(prompt) if secret and sys.stdin.isatty() else input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit("config canceled")
        value = value.strip()
        if default and not value:
            return default
        if value:
            return value
        print(f"{label.split('] ', 1)[1]} cannot be empty.")


def interactive_config() -> None:
    endpoint = prompt_value("[1/3] Image API endpoint")
    if error := endpoint_error(endpoint):
        sys.exit(f"config error: endpoint {error}")
    apikey = prompt_value("[2/3] Image API apikey", secret=True)
    model_name = prompt_value("[3/3] Image model name", default=DEFAULT_MODEL)

    print(f"\nConfirm {SETTINGS_PATH.name}:")
    print(f"  endpoint host = {display_endpoint(endpoint)}")
    print(f"  apikey        = {display_key(apikey)}")
    print(f"  model_name    = {model_name}")
    try:
        answer = input("Write this configuration? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit("config canceled")
    if answer not in ("y", "yes"):
        sys.exit("config canceled")
    write_settings(
        {
            "endpoint": normalized_field("endpoint", endpoint),
            "apikey": apikey,
            "model_name": model_name,
        }
    )
    print(f"config written: {SETTINGS_PATH}")


def noninteractive_config(values: list[str]) -> None:
    data = read_settings()
    if not str(data.get("model_name") or "").strip():
        data["model_name"] = DEFAULT_MODEL
    for item in values:
        if "=" not in item:
            sys.exit("config error: --set expects FIELD=VALUE (endpoint, apikey, or model_name)")
        name, value = item.split("=", 1)
        if name not in FIELDS:
            sys.exit("config error: supported fields are endpoint, apikey, and model_name")
        data[name] = normalized_field(name, value)
    validate_values(data, fail_fast=True)
    write_settings(data)
    print(f"config written: {SETTINGS_PATH}")


def check_config() -> None:
    data = read_settings()
    values = {name: normalized_field(name, str(data.get(name) or "")) for name in FIELDS}
    missing = [name for name in FIELDS if not values[name]]
    invalid = []
    if values["endpoint"] and endpoint_error(values["endpoint"]):
        invalid.append("endpoint")
    if missing or invalid:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if invalid:
            details.append("invalid " + ", ".join(invalid))
        print("config incomplete: " + "; ".join(details))
        raise SystemExit(1)
    print(
        f"config ok: {display_endpoint(values['endpoint'])} "
        f"key=***{values['apikey'][-4:]} model={values['model_name']}"
    )


def main(argv: list[str]) -> None:
    parser = SafeArgumentParser(prog="run.py config")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--set", action="append", default=[], metavar="FIELD=VALUE")
    args = parser.parse_args(argv)
    if args.check and args.set:
        parser.error("--check cannot be combined with --set")
    if args.check:
        check_config()
    elif args.set:
        noninteractive_config(args.set)
    else:
        interactive_config()


