"""No JS test file exercises `membersGroupedByCube` (checked the full
cubejs-client-core test suite) — this is a hand-verified unit test against a
minimal meta fixture, transcribing the exact reduce/switch logic in
Meta.ts:118-162 (one CubeMemberWrapper per cube per member-type key, with
`timeDimensions` filtered from `dimensions` by `type == 'time'`)."""

from cubejs_client.core.meta import Meta


def _meta_response():
    return {
        "cubes": [
            {
                "name": "Orders",
                "title": "Orders",
                "type": "cube",
                "public": True,
                "measures": [{"name": "Orders.count", "title": "Orders Count", "type": "number"}],
                "dimensions": [
                    {"name": "Orders.status", "title": "Orders Status", "type": "string"},
                    {"name": "Orders.createdAt", "title": "Orders Created At", "type": "time"},
                ],
                "segments": [{"name": "Orders.completed", "title": "Completed"}],
            },
            {
                "name": "Users",
                "title": "Users",
                "type": "view",
                "public": False,
                "measures": [],
                "dimensions": [{"name": "Users.country", "title": "Users Country", "type": "string"}],
                "segments": [],
            },
        ]
    }


def test_members_grouped_by_cube_groups_by_cube_and_type():
    meta = Meta(_meta_response())

    grouped = meta.members_grouped_by_cube()

    assert grouped["measures"] == [
        {
            "cubeName": "Orders",
            "cubeTitle": "Orders",
            "type": "cube",
            "public": True,
            "members": [{"name": "Orders.count", "title": "Orders Count", "type": "number"}],
        },
        {"cubeName": "Users", "cubeTitle": "Users", "type": "view", "public": False, "members": []},
    ]

    assert grouped["dimensions"] == [
        {
            "cubeName": "Orders",
            "cubeTitle": "Orders",
            "type": "cube",
            "public": True,
            "members": [
                {"name": "Orders.status", "title": "Orders Status", "type": "string"},
                {"name": "Orders.createdAt", "title": "Orders Created At", "type": "time"},
            ],
        },
        {
            "cubeName": "Users",
            "cubeTitle": "Users",
            "type": "view",
            "public": False,
            "members": [{"name": "Users.country", "title": "Users Country", "type": "string"}],
        },
    ]

    assert grouped["segments"] == [
        {
            "cubeName": "Orders",
            "cubeTitle": "Orders",
            "type": "cube",
            "public": True,
            "members": [{"name": "Orders.completed", "title": "Completed"}],
        },
        {"cubeName": "Users", "cubeTitle": "Users", "type": "view", "public": False, "members": []},
    ]

    assert grouped["timeDimensions"] == [
        {
            "cubeName": "Orders",
            "cubeTitle": "Orders",
            "type": "cube",
            "public": True,
            "members": [{"name": "Orders.createdAt", "title": "Orders Created At", "type": "time"}],
        },
        {"cubeName": "Users", "cubeTitle": "Users", "type": "view", "public": False, "members": []},
    ]


def test_members_grouped_by_cube_with_no_cubes_returns_empty_groups():
    meta = Meta({"cubes": []})

    assert meta.members_grouped_by_cube() == {"measures": [], "dimensions": [], "segments": [], "timeDimensions": []}
