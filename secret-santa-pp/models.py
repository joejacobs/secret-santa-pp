from copy import deepcopy
from typing import Any, Literal

import networkx as nx
from matplotlib import pyplot as plt
from pydantic import BaseModel, ConfigDict, EmailStr


class Person(BaseModel):
    name: str
    email: EmailStr
    relationships: dict[str, list[str]] = {}


class Constraint(BaseModel):
    relationship: str
    comparator: Literal["one-way contains", "two-way contains", "equality"]
    limit: Literal["exclude", "low-probability", "medium-probability"]

    def meet_criterion(self, src_person: Person, dst_person: Person) -> bool:
        src_relationship = src_person.relationships.get(self.relationship)
        if src_relationship is None:
            return False

        dst_relationship = dst_person.relationships.get(self.relationship, [])

        if self.comparator == "equality":
            return src_relationship == dst_relationship

        meet_criterion = dst_person.name in src_relationship

        if self.comparator == "two-way contains":
            meet_criterion |= src_person.name in dst_relationship

        return meet_criterion


class Config(BaseModel):
    people: list[Person]
    constraints: list[Constraint]


def tsp_solver(graph: nx.DiGraph, weight: str) -> list[str]:
    return nx.approximation.simulated_annealing_tsp(
        graph, "greedy", weight=weight, max_iterations=100, N_inner=1000
    )


class Solution(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Config
    n_recipients: int
    graph: nx.DiGraph = nx.DiGraph()

    @classmethod
    def generate(cls, config: Config, n_recipients: int) -> "Solution":
        solution = cls(config=config, n_recipients=n_recipients)
        solution._init_graph()
        solution._generate_solution()
        return solution

    @classmethod
    def load(cls, config: Config, solution_key: str) -> "Solution":
        pass

    def _init_graph(self) -> None:
        n_people = len(self.config.people)
        for id1 in range(n_people):
            person1 = self.config.people[id1]

            for id2 in range(id1 + 1, n_people):
                person2 = self.config.people[id2]

                if (weight := self._get_edge_weight(person1, person2)) > 0:
                    self.graph.add_edge(person1.name, person2.name, weight=weight)

                if (weight := self._get_edge_weight(person2, person1)) > 0:
                    self.graph.add_edge(person2.name, person1.name, weight=weight)

    def _get_edge_weight(self, src_person: Person, dst_person: Person) -> int:
        weight = 1

        if len(src_person.relationships) == 0:
            return weight

        for constraint in self.config.constraints:
            if constraint.meet_criterion(src_person, dst_person):
                if constraint.limit == "exclude":
                    return -1

                if constraint.limit == "low-probability":
                    weight += 4
                elif constraint.limit == "medium-probability":
                    weight += 2

        return weight

    def _generate_solution(self) -> None:
        final_graph = nx.DiGraph()
        init_graph = deepcopy(self.graph)
        for _ in range(self.n_recipients):
            tsp_path = nx.approximation.traveling_salesman_problem(
                deepcopy(init_graph), cycle=True, method=tsp_solver
            )

            for src, dst in zip(tsp_path[:-1], tsp_path[1:]):
                final_graph.add_edge(src, dst, weight=self.graph[src][dst]["weight"])
                init_graph.remove_edge(src, dst)

        for node in final_graph.nodes:
            if (
                final_graph.in_degree(node) != self.n_recipients
                or final_graph.out_degree(node) != self.n_recipients
            ):
                msg = f"Invalid solution: {final_graph.edges}"
                raise RuntimeError(msg)

        self.graph = final_graph

    def display(self) -> None:
        pos = nx.shell_layout(self.graph)
        nx.draw(self.graph, pos, node_size=1000, font_size=16)
        nx.draw_networkx_labels(self.graph, pos)
        plt.show()
