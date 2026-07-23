from cubejs_client.query.builder import dim, measure
from cubejs_client.query.model import Query


def test_query_builder_produces_cube_api_query_shape():
    q = (
        Query()
        .measures("Orders.count")
        .dimensions("Users.city")
        .time_dimension("Orders.createdAt", granularity="month", date_range=["2020-01-01", "2020-12-31"])
        .filter(dim("Users.status") == "completed")
        .order("Orders.count", "desc")
        .limit(100)
    )

    assert q.build() == {
        "measures": ["Orders.count"],
        "dimensions": ["Users.city"],
        "timeDimensions": [
            {
                "dimension": "Orders.createdAt",
                "granularity": "month",
                "dateRange": ["2020-01-01", "2020-12-31"],
            }
        ],
        "filters": [{"member": "Users.status", "operator": "equals", "values": ["completed"]}],
        "order": [["Orders.count", "desc"]],
        "limit": 100,
    }


def test_query_builder_is_immutable_across_calls():
    base = Query().measures("Orders.count")
    with_limit = base.limit(10)

    assert base.build() == {"measures": ["Orders.count"]}
    assert with_limit.build() == {"measures": ["Orders.count"], "limit": 10}


def test_member_comparison_operators_build_filters():
    assert (dim("Users.age") >= 21) == {
        "member": "Users.age",
        "operator": "gte",
        "values": ["21"],
    }
    assert dim("Users.name").contains("a") == {
        "member": "Users.name",
        "operator": "contains",
        "values": ["a"],
    }
    assert measure("Orders.count").is_set() == {"member": "Orders.count", "operator": "set"}


def test_boolean_filter_values_are_lowercased():
    assert (dim("Users.active") == True) == {  # noqa: E712
        "member": "Users.active",
        "operator": "equals",
        "values": ["true"],
    }
    assert (dim("Users.active") == False) == {  # noqa: E712
        "member": "Users.active",
        "operator": "equals",
        "values": ["false"],
    }


def test_equality_with_none_routes_to_set_operators():
    assert (dim("Users.email") == None) == {"member": "Users.email", "operator": "notSet"}  # noqa: E711
    assert (dim("Users.email") != None) == {"member": "Users.email", "operator": "set"}  # noqa: E711


def test_filters_combine_with_and_or_operators():
    f1 = dim("Users.status") == "completed"
    f2 = dim("Users.city") == "NYC"

    assert (f1 & f2) == {
        "and": [
            {"member": "Users.status", "operator": "equals", "values": ["completed"]},
            {"member": "Users.city", "operator": "equals", "values": ["NYC"]},
        ]
    }
    assert (f1 | f2) == {
        "or": [
            {"member": "Users.status", "operator": "equals", "values": ["completed"]},
            {"member": "Users.city", "operator": "equals", "values": ["NYC"]},
        ]
    }
