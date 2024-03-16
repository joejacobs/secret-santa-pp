from abc import ABC, abstractmethod
from dataclasses import field
from typing import Generic, TypeVar

from pydantic import BaseModel, EmailStr

from secret_santa_pp.config import (
    ComparatorType,
    Config,
    Constraint,
    LimitType,
    Person,
)

T = TypeVar("T")


class Mock(ABC, BaseModel, Generic[T]):
    model: T | None = None

    def get_model(self) -> T:
        if self.model is None:
            self.model = self._create_model()

        return self.model

    @abstractmethod
    def _create_model(self) -> T:
        pass

    @abstractmethod
    def assert_equivalent(self, other: T) -> None:
        pass


class MockPerson(Mock[Person]):
    name: str = "name"
    email: EmailStr = "person@example.com"
    relationships: dict[str, list[str]] = field(default_factory=dict)

    def _create_model(self) -> Person:
        return Person(
            name=self.name,
            email=self.email,
            relationships=self.relationships,
        )

    def assert_equivalent(self, other: Person) -> None:
        assert self.name == other.name
        assert self.email == other.email
        assert self.relationships == other.relationships


class MockConstraint(Mock[Constraint]):
    relationship_key: str = "relationship-key"
    comparator: ComparatorType = "one-way contains"
    limit: LimitType = "exclude"

    def _create_model(self) -> Constraint:
        return Constraint(
            relationship_key=self.relationship_key,
            comparator=self.comparator,
            limit=self.limit,
        )

    def assert_equivalent(self, other: Constraint) -> None:
        assert self.relationship_key == other.relationship_key
        assert self.comparator == other.comparator
        assert self.limit == other.limit


class MockConfig(Mock[Config]):
    people: list[MockPerson] = field(default_factory=list)
    constraints: list[MockConstraint] = field(default_factory=list)

    def _create_model(self) -> Config:
        return Config(
            people=[person.get_model() for person in self.people],
            constraints=[constraint.get_model() for constraint in self.constraints],
        )

    def assert_equivalent(self, other: Config) -> None:
        for person, other_person in zip(self.people, other.people, strict=True):
            person.assert_equivalent(other_person)

        for constraint, other_constraint in zip(
            self.constraints, other.constraints, strict=True
        ):
            constraint.assert_equivalent(other_constraint)
