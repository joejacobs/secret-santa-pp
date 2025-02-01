from __future__ import annotations

from copy import deepcopy
from itertools import pairwise
from typing import Any, cast

from matplotlib import pyplot as plt
from networkx import (
    approximation,
    draw,  # pyright: ignore [reportUnknownVariableType]
    draw_networkx_labels,  # pyright: ignore [reportUnknownVariableType]
    shell_layout,  # pyright: ignore [reportUnknownVariableType]
)
from pydantic import BaseModel, ConfigDict
from rich.console import Console

from secret_santa_pp.config import Config, Constraint, Person
from secret_santa_pp.wrapper import DiGraph


def get_edge_weight(
    constraints: list[Constraint], src_person: Person, dst_person: Person
) -> int | None:
    weight = 1

    if len(src_person.relationships) == 0:
        return weight

    for constraint in constraints:
        if constraint.meet_criterion(src_person, dst_person):
            if constraint.limit == "exclude":
                return None

            if constraint.limit == "low-probability":
                weight += 4
            elif constraint.limit == "medium-probability":
                weight += 2

    return weight


def tsp_solver(graph: DiGraph[str], weight: str) -> list[str]:
    return cast(
        list[str],
        approximation.simulated_annealing_tsp(  # pyright: ignore [reportUnknownMemberType]
            graph, "greedy", weight=weight, max_iterations=100, N_inner=1000
        ),
    )


class Solution(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    graph: DiGraph[str]

    @classmethod
    def generate(
        cls, config: Config, participants: list[str] | None, n_recipients: int
    ) -> Solution:
        solution = cls(graph=DiGraph())
        solution.init_graph(config, participants)
        solution.generate_solution(n_recipients)
        return solution

    @classmethod
    def load(cls, config: Config, solution_key: str) -> Solution:
        graph = config.load_graph(solution_key)
        if len(graph.edges) == 0:
            msg = f"Solution key not found: {solution_key}."
            raise LookupError(msg)

        return cls(graph=graph)

    def init_graph(self, config: Config, participants: list[str] | None) -> None:
        people = [
            person
            for person in config.people
            if participants is None or person.name in participants
        ]
        n_people = len(people)
        for i in range(n_people):
            person1 = people[i]

            for j in range(i + 1, n_people):
                person2 = people[j]

                if (
                    weight := get_edge_weight(config.constraints, person1, person2)
                ) is not None:
                    self.graph.add_edge(  # pyright: ignore [reportUnknownMemberType]
                        person1.name, person2.name, weight=weight
                    )

                if (
                    weight := get_edge_weight(config.constraints, person2, person1)
                ) is not None:
                    self.graph.add_edge(  # pyright: ignore [reportUnknownMemberType]
                        person2.name, person1.name, weight=weight
                    )

    def generate_solution(self, n_recipients: int) -> None:
        final_graph: DiGraph[str] = DiGraph()
        init_graph = deepcopy(self.graph)
        for _ in range(n_recipients):
            tsp_path: list[str] = cast(
                list[str],
                approximation.traveling_salesman_problem(  # pyright: ignore [reportUnknownMemberType]
                    deepcopy(init_graph), cycle=True, method=tsp_solver
                ),
            )

            for src, dst in pairwise(tsp_path):
                final_graph.add_edge(  # pyright: ignore [reportUnknownMemberType]
                    src, dst, weight=self.graph[src][dst]["weight"]
                )
                init_graph.remove_edge(src, dst)

        self.graph = final_graph
        self._verify_solution(n_recipients)

    def _verify_solution(self, n_recipients: int) -> None:
        if len(self.graph.nodes) == 0:
            msg = "Invalid solution: empty graph"
            raise RuntimeError(msg)

        for node in self.graph.nodes:
            if (
                cast(int, self.graph.in_degree(node)) != n_recipients
                or cast(int, self.graph.out_degree(node)) != n_recipients
            ):
                msg = f"Invalid solution: {self.graph.edges}"
                raise RuntimeError(msg)

    def visualise(self) -> None:
        pos: Any = shell_layout(self.graph)
        draw(self.graph, pos, node_size=1000, font_size=16)
        draw_networkx_labels(self.graph, pos)
        plt.show()  # pyright: ignore [reportUnknownMemberType]

    def print(self) -> None:
        console = Console()
        for s in self.graph:
            edges = list(self.graph[s])
            console.print(f"{s}: {', '.join(edges)}")
