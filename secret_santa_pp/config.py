from typing import Literal

import networkx as nx
from pydantic import BaseModel, EmailStr

ComparatorType = Literal[
    "one-way contains", "two-way contains", "either contains", "equality"
]
LimitType = Literal["exclude", "low-probability", "medium-probability"]


class Person(BaseModel):
    name: str
    email: EmailStr
    relationships: dict[str, list[str]] = {}


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


class Config(BaseModel):
    people: list[Person]
    constraints: list[Constraint]

    def update_with_graph(self, graph: nx.DiGraph, key: str) -> None:
        for person in self.people:
            if person.name in graph.nodes:
                person.relationships[key] = list(graph[person.name])

    def load_graph(self, key: str) -> nx.DiGraph:
        graph = nx.DiGraph()
        for person in self.people:
            for recipient in person.relationships.get(key, []):
                graph.add_edge(person.name, recipient)

        return graph
