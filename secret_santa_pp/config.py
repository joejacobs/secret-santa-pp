from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr

from secret_santa_pp.wrapper import DiGraph

type ComparatorType = Literal[
    "one-way contains", "two-way contains", "either contains", "equality"
]
type LimitType = Literal["exclude", "low-probability", "medium-probability"]


class Person(BaseModel):
    name: str
    email: EmailStr
    relationships: dict[str, list[str]] = {}


class Config(BaseModel):
    people: list[Person]
    constraints: list[Constraint]

    def update_from_graph(self, graph: DiGraph[str], key: str) -> None:
        for person in self.people:
            if person.name in graph.nodes:
                person.relationships[key] = list(graph[person.name])

    def load_graph(self, key: str) -> DiGraph[str]:
        return DiGraph(
            [
                (person.name, recipient)
                for person in self.people
                for recipient in person.relationships.get(key, [])
            ]
        )


class Constraint(BaseModel):
    relationship_key: str
    comparator: ComparatorType
    limit: LimitType

    def meet_criterion(self, src_person: Person, dst_person: Person) -> bool:
        if (
            len(
                src_relationship := src_person.relationships.get(
                    self.relationship_key, []
                )
            )
            == 0
        ):
            return False

        dst_relationship = dst_person.relationships.get(self.relationship_key, [])

        if self.comparator == "equality":
            return len(dst_relationship) > 0 and src_relationship == dst_relationship

        meet_criterion = dst_person.name in src_relationship

        if self.comparator == "one-way contains":
            return meet_criterion

        opposite_contains = (
            len(dst_relationship) > 0 and src_person.name in dst_relationship
        )

        if self.comparator == "either contains":
            meet_criterion |= opposite_contains
        elif self.comparator == "two-way contains":
            meet_criterion &= opposite_contains

        return meet_criterion
