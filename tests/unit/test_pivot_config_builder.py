import pytest

from cubejs_client.core.result_set import ResultSet
from cubejs_client.query.pivot_config import PivotConfig, to_pivot_config_dict


def test_pivot_config_builder_produces_camel_case_dict():
    pc = (
        PivotConfig()
        .x("Orders.createdAt.day")
        .y("Users.country", "measures")
        .fill_missing_dates(True)
        .join_date_range(True)
        .fill_with_value(0)
        .alias_series("one", "two")
    )

    assert pc.build() == {
        "x": ["Orders.createdAt.day"],
        "y": ["Users.country", "measures"],
        "fillMissingDates": True,
        "joinDateRange": True,
        "fillWithValue": 0,
        "aliasSeries": ["one", "two"],
    }


def test_pivot_config_builder_is_immutable():
    base = PivotConfig().x("A")
    derived = base.y("B")

    assert base.build() == {"x": ["A"]}
    assert derived.build() == {"x": ["A"], "y": ["B"]}


def test_empty_pivot_config_builds_to_empty_dict_not_none():
    # Mirrors JS `pivotConfig || {defaultXY}`: an explicitly-constructed
    # PivotConfig (even with no fields) is a truthy object and must skip the
    # x/y smart default, exactly like an explicit `{}`.
    assert PivotConfig().build() == {}


def test_to_pivot_config_dict_passes_none_through():
    assert to_pivot_config_dict(None) is None


def test_to_pivot_config_dict_converts_pivot_config_instance():
    assert to_pivot_config_dict(PivotConfig().x("A")) == {"x": ["A"]}


def test_to_pivot_config_dict_copies_plain_dict():
    original = {"x": ["A"]}
    result = to_pivot_config_dict(original)
    assert result == original
    assert result is not original


def test_result_set_pivot_rejects_pivot_config_instance_with_clear_error():
    # ResultSet's core methods only accept plain dicts (mirroring how they
    # never accept a `Query` object either) — passing a `PivotConfig` should
    # fail loudly with actionable guidance, not deep inside merge_deep_left.
    rs = ResultSet(
        {
            "query": {"measures": ["Foo.count"]},
            "data": [{"Foo.count": 1}],
            "annotation": {
                "measures": {"Foo.count": {"title": "Count", "shortTitle": "Count", "type": "number"}},
                "dimensions": {},
                "segments": {},
                "timeDimensions": {},
            },
        }
    )

    with pytest.raises(TypeError, match="build"):
        rs.pivot(PivotConfig().x("Foo.count"))
