import re

import pytest

from secret_santa_pp.config import Config
from secret_santa_pp.solution import Solution
from secret_santa_pp.wrapper import DiGraph


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
        (
            [("a", "b"), ("a", "c"), ("b", "a"), ("b", "c"), ("c", "a")],
            2,
            True,
        ),
        (
            [("a", "b"), ("a", "c"), ("b", "c")],
            3,
            True,
        ),
    ],
)
def test_solution_verify_solution(
    edges: list[tuple[str, str]], n_recipients: int, expect_error: bool
):
    graph: DiGraph[str] = DiGraph()
    graph.add_edges_from(edges)  # pyright: ignore[reportUnknownMemberType]

    solution = Solution(config=Config(people=[], constraints=[]), graph=graph)

    if expect_error is True:
        error_msg = f"Invalid solution: {edges}"
        with pytest.raises(RuntimeError, match=re.escape(error_msg)):
            solution._verify_solution(  # pyright: ignore[reportPrivateUsage]
                n_recipients
            )
    else:
        solution._verify_solution(n_recipients)  # pyright: ignore[reportPrivateUsage]


def test_solution_verify_solution_empty_graph_raises_error():
    solution = Solution(
        config=Config(people=[], constraints=[]),
        graph=DiGraph(),
    )

    with pytest.raises(RuntimeError, match="Invalid solution: empty graph"):
        solution._verify_solution(n_recipients=1)  # pyright: ignore[reportPrivateUsage]
