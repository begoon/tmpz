from typing import Any


def _build_key(
    previous_key: str | None,
    separator: str,
    new_key: str | int,
    replace_separators: str | None = None,
) -> str:
    new_key_str = str(new_key)
    if replace_separators is not None:
        new_key_str = new_key_str.replace(separator, replace_separators)
    if previous_key:
        return f"{previous_key}{separator}{new_key_str}"
    return new_key_str


def flatten(
    nested_dict: dict[str, Any],
    separator: str = "_",
    root_keys_to_ignore: set[str] | None = None,
    replace_separators: str | None = None,
) -> dict[str, Any]:
    if not isinstance(nested_dict, dict):
        raise TypeError("flatten requires a dictionary input")

    if not nested_dict:
        return {}

    if root_keys_to_ignore is None:
        root_keys_to_ignore = set()

    flattened_dict: dict[str, Any] = {}

    def _flatten(obj: Any, key: str | None) -> None:
        if not obj:
            if key is not None:
                flattened_dict[key] = obj
        elif isinstance(obj, dict):
            for obj_key, obj_val in obj.items():
                if key or obj_key not in root_keys_to_ignore:
                    _flatten(
                        obj_val,
                        _build_key(key, separator, obj_key, replace_separators),
                    )
        elif isinstance(obj, (list, set, tuple)):
            for index, item in enumerate(obj):
                _flatten(
                    item,
                    _build_key(key, separator, index, replace_separators),
                )
        else:
            if key is not None:
                flattened_dict[key] = obj

    _flatten(nested_dict, None)
    return flattened_dict
