from cubejs_client.core.response_decode import decode_response_data


def _annotation():
    return {
        "measures": {"Orders.count": {"title": "Count", "shortTitle": "Count", "type": "number"}},
        "dimensions": {"Orders.status": {"title": "Status", "shortTitle": "Status", "type": "string"}},
        "segments": {},
        "timeDimensions": {},
    }


def test_compact_response_format_unpacks_to_row_dicts():
    response = {
        "results": [
            {
                "query": {"responseFormat": "compact"},
                "annotation": _annotation(),
                "data": {
                    "members": ["Orders.status", "Orders.count"],
                    "dataset": [["completed", "5"], ["shipped", "3"]],
                },
            }
        ]
    }

    decode_response_data(response)

    assert response["results"][0]["data"] == [
        {"Orders.status": "completed", "Orders.count": "5"},
        {"Orders.status": "shipped", "Orders.count": "3"},
    ]


def test_columnar_response_format_unpacks_to_row_dicts():
    response = {
        "results": [
            {
                "query": {"responseFormat": "columnar"},
                "annotation": _annotation(),
                "data": {
                    "members": ["Orders.status", "Orders.count"],
                    "columns": [["completed", "shipped"], ["5", "3"]],
                },
            }
        ]
    }

    decode_response_data(response)

    assert response["results"][0]["data"] == [
        {"Orders.status": "completed", "Orders.count": "5"},
        {"Orders.status": "shipped", "Orders.count": "3"},
    ]


def test_cast_numerics_converts_number_typed_members_in_default_format():
    response = {
        "results": [
            {
                "query": {},
                "annotation": _annotation(),
                "data": [
                    {"Orders.status": "completed", "Orders.count": "5"},
                    {"Orders.status": "shipped", "Orders.count": None},
                ],
            }
        ]
    }

    decode_response_data(response, cast_numerics=True)

    assert response["results"][0]["data"] == [
        {"Orders.status": "completed", "Orders.count": 5},
        {"Orders.status": "shipped", "Orders.count": None},
    ]


def test_no_results_is_a_no_op():
    response = {"results": []}

    decode_response_data(response, cast_numerics=True)

    assert response == {"results": []}
