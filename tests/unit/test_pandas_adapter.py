from cubejs_client.core.result_set import ResultSet


def _make_result_set():
    return ResultSet(
        {
            "query": {"measures": ["Foo.count"], "dimensions": ["Foo.name"]},
            "data": [
                {"Foo.name": "A", "Foo.count": "1"},
                {"Foo.name": "B", "Foo.count": "2"},
            ],
            "annotation": {
                "measures": {"Foo.count": {"title": "Foo Count", "shortTitle": "Count", "type": "number"}},
                "dimensions": {"Foo.name": {"title": "Foo Name", "shortTitle": "Name", "type": "string"}},
                "segments": {},
                "timeDimensions": {},
            },
        }
    )


def test_to_pandas_table_matches_table_pivot_rows():
    rs = _make_result_set()

    df = rs.to_pandas()

    assert list(df["Foo.name"]) == ["A", "B"]
    assert list(df["Foo.count"]) == [1, 2]


def test_df_property_is_equivalent_to_to_pandas_default():
    rs = _make_result_set()

    assert rs.df.equals(rs.to_pandas())


def test_to_pandas_chart_kind_matches_chart_pivot_rows():
    rs = _make_result_set()

    df = rs.to_pandas(kind="chart")

    assert list(df["x"]) == ["A", "B"]
    assert list(df["Foo.count"]) == [1, 2]
