from typing import Literal

import networkx as nx
import numpy as np
from pydantic import BaseModel, ConfigDict, EmailStr


class Person(BaseModel):
    name: str
    email: EmailStr
    relationships: dict[str, list[str]] = {}


class LimitCriterion(BaseModel):
    relationship: str
    comparator: Literal["one-way contains", "two-way contains", "equality"]
    limit: Literal["exclude", "low-probability", "medium-probability"]

    def meet(self, src_person: Person, dst_person: Person) -> bool:
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


class PeopleGraph(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    graph: nx.DiGraph
    people: list[Person]
    limit_criteria: list[LimitCriterion]
    rng: np.random.Generator

    def __init__(
        self, people: list[Person], limits: list[LimitCriterion], seed: int = 0
    ) -> None:
        super().__init__(
            graph=nx.DiGraph(),
            people=people,
            limit_criteria=limits,
            rng=np.random.default_rng(seed=seed),
        )

    def random_init(self) -> None:
        n_people = len(self.people)
        for id1 in range(n_people):
            person1 = self.people[id1]

            for id2 in range(id1 + 1, n_people):
                person2 = self.people[id2]

                self.graph.add_edge(
                    person1.name,
                    person2.name,
                    weight=self._get_edge_weight(person1, person2),
                )
                self.graph.add_edge(
                    person2.name,
                    person1.name,
                    weight=self._get_edge_weight(person2, person1),
                )

    def _get_edge_weight(self, src_person: Person, dst_person: Person) -> float:
        weight = self.rng.uniform(0.7, 1)

        if len(src_person.relationships) == 0:
            return weight

        for criterion in self.limit_criteria:
            if criterion.meet(src_person, dst_person):
                if criterion.limit == "exclude":
                    return 0

                if criterion.limit == "low-probability":
                    weight -= self.rng.uniform(0.2, 0.4)

                if criterion.limit == "medium-probability":
                    weight -= self.rng.uniform(0.05, 0.1)

        return (1 - max(0, weight)) * 100

    def solve(self, solution_key: str, n_recipients: int) -> None:
        initial_graph = self.graph.copy()
        final_solution = nx.DiGraph()

        for _ in range(n_recipients):
            solution = nx.approximation.traveling_salesman_problem(initial_graph)
            initial_graph.remove_edges_from(solution.edges)
            final_solution.add_edges_from(solution.edges)

        self.graph = final_solution

        for person in self.people:
            person.relationships[solution_key] = sorted(
                list(final_solution.neighbors(person.name))
            )
