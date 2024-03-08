from typing import Literal

import numpy as np
from numpy.typing import NDArray
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

    nodes: list[Person]
    edges: NDArray[np.float64]
    limit_criteria: list[LimitCriterion]
    rng: np.random.Generator

    def __init__(
        self, people: list[Person], limits: list[LimitCriterion], seed: int = 0
    ) -> None:
        super().__init__(
            nodes=people,
            edges=np.zeros((len(people), len(people))),
            rng=np.random.default_rng(seed=seed),
            limit_criteria=limits,
        )

    def random_init(self) -> None:
        for src_id in range(self.edges.shape[0]):
            src_person = self.nodes[src_id]

            for dst_id in range(self.edges.shape[1]):
                if dst_id == src_id:
                    continue

                dst_person = self.nodes[dst_id]

                self.edges[src_id, dst_id] = self._get_edge_weight(
                    src_person, dst_person
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

        return max(0, weight)
