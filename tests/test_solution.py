import re

import pytest

from secret_santa_pp.config import ComparatorType, LimitType
from secret_santa_pp.solution import Solution, get_edge_weight
from secret_santa_pp.wrapper import DiGraph

from tests.helper.config import MockConfig, MockConstraint, MockPerson


@pytest.mark.parametrize(
    ("src_relationships", "constraint_params", "expected_weight"),
    [
        ({}, [], 1),
        ({"key": ["b"]}, [("key", "one-way contains", "exclude")], None),
        ({"key": ["b"]}, [("key", "one-way contains", "low-probability")], 5),
        ({"key": ["b"]}, [("key", "one-way contains", "medium-probability")], 3),
        ({"key": ["b"]}, [("other-key", "one-way contains", "medium-probability")], 1),
        (
            {"key-0": ["b"], "key-1": ["b"]},
            [
                ("key-0", "one-way contains", "low-probability"),
                ("key-1", "one-way contains", "medium-probability"),
            ],
            7,
        ),
        (
            {"key-0": ["b"], "key-1": ["b"]},
            [
                ("key-0", "one-way contains", "low-probability"),
                ("key-1", "one-way contains", "exclude"),
            ],
            None,
        ),
        ({"key-0": ["b"]}, [("key-1", "one-way contains", "low-probability")], 1),
    ],
)
def test_get_edge_weight(
    src_relationships: dict[str, list[str]],
    constraint_params: list[tuple[str, ComparatorType, LimitType]],
    expected_weight: int | None,
):
    src_person = MockPerson(name="a", relationships=src_relationships).get_model()
    dst_person = MockPerson(name="b").get_model()

    constraints = [
        MockConstraint(
            relationship_key=relationship_key,
            comparator=comparator_type,
            limit=limit_type,
        ).get_model()
        for relationship_key, comparator_type, limit_type in constraint_params
    ]

    assert get_edge_weight(constraints, src_person, dst_person) == expected_weight


def test_solution_load():
    path = [str(i) for i in range(5)] + [str(i) for i in range(2)]
    src_dst_list_map = {
        i: [j, k] for i, j, k in zip(path[:-2], path[1:-1], path[2:], strict=True)
    }

    config = MockConfig(
        people=[
            MockPerson(
                name=str(i),
                relationships={"graph-key": src_dst_list_map.get(str(i), [])},
            )
            for i in range(10)
        ]
    ).get_model()

    solution = Solution.load(config, "graph-key")

    assert len(solution.graph.nodes) == len(src_dst_list_map)
    for node in solution.graph.nodes:
        assert list(solution.graph[node]) == src_dst_list_map[node]


def test_solution_load_key_not_found():
    config = MockConfig(people=[]).get_model()

    with pytest.raises(LookupError, match="Solution key not found: invalid-key"):
        Solution.load(config, "invalid-key")


@pytest.mark.parametrize(
    ("edges", "n_recipients", "expect_error"),
    [
        (
            [("a", "b"), ("a", "c"), ("b", "a"), ("b", "c"), ("c", "a"), ("c", "b")],
            2,
            False,
        ),
        (
            [("a", "b"), ("a", "c"), ("b", "a"), ("b", "c"), ("c", "a"), ("c", "b")],
            3,
            True,
        ),
        ([("a", "b"), ("a", "c"), ("b", "a"), ("b", "c"), ("c", "a")], 2, True),
        ([("a", "b"), ("a", "c"), ("b", "c")], 3, True),
    ],
)
def test_solution_verify_solution(
    edges: list[tuple[str, str]], n_recipients: int, expect_error: bool
):
    graph: DiGraph[str] = DiGraph()
    graph.add_edges_from(edges)  # pyright: ignore[reportUnknownMemberType]

    solution = Solution(graph=graph)

    if expect_error is True:
        error_msg = f"Invalid solution: {edges}"
        with pytest.raises(RuntimeError, match=re.escape(error_msg)):
            solution._verify_solution(  # pyright: ignore[reportPrivateUsage]
                n_recipients
            )
    else:
        solution._verify_solution(n_recipients)  # pyright: ignore[reportPrivateUsage]


def test_solution_verify_solution_empty_graph_raises_error():
    solution = Solution(graph=DiGraph())

    with pytest.raises(RuntimeError, match="Invalid solution: empty graph"):
        solution._verify_solution(n_recipients=1)  # pyright: ignore[reportPrivateUsage]
