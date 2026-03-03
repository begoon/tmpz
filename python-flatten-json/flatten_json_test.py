import pytest

from flatten_json import _build_key, flatten


class TestConstructKey:
    def test_no_previous_key(self) -> None:
        assert _build_key(None, "_", "a") == "a"

    def test_with_previous_key(self) -> None:
        assert _build_key("a", "_", "b") == "a_b"

    def test_integer_new_key(self) -> None:
        assert _build_key("items", "_", 0) == "items_0"

    def test_replace_separators(self) -> None:
        assert _build_key("a", "_", "b_c", replace_separators="-") == "a_b-c"

    def test_replace_separators_no_previous(self) -> None:
        assert _build_key(None, "_", "b_c", replace_separators="-") == "b-c"


class TestFlatten:
    def test_empty_dict(self) -> None:
        assert flatten({}) == {}

    def test_already_flat(self) -> None:
        assert flatten({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_nested_dict(self) -> None:
        assert flatten({"a": {"b": 1, "c": 2}}) == {"a_b": 1, "a_c": 2}

    def test_deeply_nested(self) -> None:
        assert flatten({"a": {"b": {"c": 3}}}) == {"a_b_c": 3}

    def test_custom_separator(self) -> None:
        assert flatten({"a": {"b": 1}}, separator=".") == {"a.b": 1}

    def test_list_values(self) -> None:
        assert flatten({"a": [1, 2, 3]}) == {"a_0": 1, "a_1": 2, "a_2": 3}

    def test_nested_list_of_dicts(self) -> None:
        result = flatten({"a": [{"b": 1}, {"b": 2}]})
        assert result == {"a_0_b": 1, "a_1_b": 2}

    def test_tuple_values(self) -> None:
        assert flatten({"a": (10, 20)}) == {"a_0": 10, "a_1": 20}

    def test_set_values(self) -> None:
        result = flatten({"a": {42}})
        assert result == {"a_0": 42}

    def test_root_keys_to_ignore(self) -> None:
        result = flatten({"a": 1, "b": {"c": 2}}, root_keys_to_ignore={"b"})
        assert result == {"a": 1}

    def test_root_keys_to_ignore_only_at_root(self) -> None:
        result = flatten({"a": {"b": {"c": 3}}}, root_keys_to_ignore={"b"})
        assert result == {"a_b_c": 3}

    def test_replace_separators(self) -> None:
        result = flatten(
            {"a_b": {"c": 1}}, separator="_", replace_separators="-"
        )
        assert result == {"a-b_c": 1}

    def test_empty_nested_dict(self) -> None:
        result = flatten({"a": {}})
        assert result == {"a": {}}

    def test_empty_nested_list(self) -> None:
        result = flatten({"a": []})
        assert result == {"a": []}

    def test_none_value(self) -> None:
        result = flatten({"a": None})
        assert result == {"a": None}

    def test_zero_value(self) -> None:
        result = flatten({"a": 0})
        assert result == {"a": 0}

    def test_false_value(self) -> None:
        result = flatten({"a": False})
        assert result == {"a": False}

    def test_string_value(self) -> None:
        result = flatten({"a": {"b": "hello"}})
        assert result == {"a_b": "hello"}

    def test_non_dict_input_raises(self) -> None:
        with pytest.raises(
            TypeError, match="flatten requires a dictionary input"
        ):
            flatten([1, 2, 3])  # type: ignore[arg-type]

    def test_mixed_nesting(self) -> None:
        data = {"a": 1, "b": {"c": [{"d": 2}]}, "e": "x"}
        result = flatten(data)
        assert result == {"a": 1, "b_c_0_d": 2, "e": "x"}
