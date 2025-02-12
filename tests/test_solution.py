from itertools import pairwise
import re

import pytest
from pytest_mock import MockerFixture

from secret_santa_pp.config import ComparatorType, LimitType
from secret_santa_pp.solution import Solution, get_edge_weight, tsp_solver
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


def test_tsp_solver(mocker: MockerFixture):
    mock_simulated_annealing_tsp = mocker.patch(
        "secret_santa_pp.solution.approximation.simulated_annealing_tsp", autospec=True
    )
    mock_simulated_annealing_tsp.return_value = ["a", "b", "c"]

    graph: DiGraph[str] = DiGraph()
    return_value = tsp_solver(graph, "weight")

    assert return_value == ["a", "b", "c"]
    mock_simulated_annealing_tsp.assert_called_once_with(
        graph, "greedy", weight="weight", max_iterations=100, N_inner=1000
    )


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


def test_solution_init_graph(mocker: MockerFixture):
    mock_get_edge_weight = mocker.patch(
        "secret_santa_pp.solution.get_edge_weight", autospec=True
    )
    mock_get_edge_weight.side_effect = list(range(1, 7))

    participants = [str(i) for i in range(3)]
    config = MockConfig(
        people=[MockPerson(name=str(i)) for i in range(5)],
    ).get_model()

    solution = Solution(graph=DiGraph())
    solution.init_graph(config, participants)

    assert len(solution.graph.nodes) == len(participants)

    weight_counter = 1
    for i, p1 in enumerate(participants):
        for p2 in participants[i + 1 :]:
            assert solution.graph[p1][p2]["weight"] == weight_counter
            weight_counter += 1

            assert solution.graph[p2][p1]["weight"] == weight_counter
            weight_counter += 1


def test_solution_init_graph_no_participants(mocker: MockerFixture):
    mock_get_edge_weight = mocker.patch(
        "secret_santa_pp.solution.get_edge_weight", autospec=True
    )
    mock_get_edge_weight.side_effect = list(range(1, 21))

    config = MockConfig(
        people=[MockPerson(name=str(i)) for i in range(5)],
    ).get_model()

    solution = Solution(graph=DiGraph())
    solution.init_graph(config, None)

    expected_participants = [str(i) for i in range(5)]
    assert len(solution.graph.nodes) == len(expected_participants)

    weight_counter = 1
    for i, p1 in enumerate(expected_participants):
        for p2 in expected_participants[i + 1 :]:
            assert solution.graph[p1][p2]["weight"] == weight_counter
            weight_counter += 1

            assert solution.graph[p2][p1]["weight"] == weight_counter
            weight_counter += 1


def test_solution_generate_solution(mocker: MockerFixture):
    paths = [
        ["0", "1", "2", "3", "4", "0"],
        ["4", "3", "2", "1", "0", "4"],
    ]
    mock_traveling_salesman_problem = mocker.patch(
        "secret_santa_pp.solution.approximation.traveling_salesman_problem",
        autospec=True,
    )
    mock_traveling_salesman_problem.side_effect = paths

    graph: DiGraph[str] = DiGraph()
    participants = [str(i) for i in range(5)]
    for i, p1 in enumerate(participants):
        for p2 in participants[i + 1 :]:
            graph.add_edge(  # pyright: ignore [reportUnknownMemberType]
                p1, p2, weight=1
            )
            graph.add_edge(  # pyright: ignore [reportUnknownMemberType]
                p2, p1, weight=1
            )

    solution = Solution(graph=graph)
    solution.generate_solution(2)

    for p in participants:
        assert solution.graph.in_degree(p) == len(paths)
        assert solution.graph.in_degree(p) == len(paths)

    for path in paths:
        for src, dst in pairwise(path):
            assert solution.graph[src][dst]["weight"] == 1


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
