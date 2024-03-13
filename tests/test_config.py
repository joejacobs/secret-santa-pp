import pytest

from secret_santa_pp.config import ComparatorType
from tests.helper.config import MockConstraint, MockPerson


@pytest.mark.parametrize(
    ("relationship_params", "comparator", "expected_result"),
    [
        *[
            (
                relationship_tuple,
                comparator,
                False,
            )
            for comparator in [
                "one-way contains",
                "two-way contains",
                "either contains",
                "equality",
            ]
            for relationship_tuple in [
                # empty relationships
                ({}, {}),
                # relationship missing from one
                ({}, {"key": []}),
                ({"key": []}, {}),
                ({"other-key": []}, {"key": []}),
                ({"key": []}, {"other-key": []}),
                # relationships missing from both
                ({"other-key": []}, {"other-key": []}),
                # both relationships empty
                ({"key": []}, {"key": []}),
            ]
        ],
        # one-way contains relationship
        *[
            (
                relationship_tuple,
                comparator,
                comparator in ["one-way contains", "either contains"],
            )
            for comparator in [
                "one-way contains",
                "two-way contains",
                "either contains",
                "equality",
            ]
            for relationship_tuple in [
                (
                    {"key": ["person-2", "person-3"], "other-key": ["person-3"]},
                    {"other-key": ["person-2"]},
                ),
                (
                    {"key": ["person-2", "person-3"], "other-key": ["person-3"]},
                    {"key": [], "other-key": ["person-3"]},
                ),
                (
                    {"key": ["person-2", "person-3"], "other-key": ["person-3"]},
                    {"key": ["person-3"], "other-key": ["person-3"]},
                ),
            ]
        ],
        # two-way contains relationship
        *[
            (
                relationship_tuple,
                comparator,
                comparator
                in ["one-way contains", "two-way contains", "either contains"],
            )
            for comparator in [
                "one-way contains",
                "two-way contains",
                "either contains",
                "equality",
            ]
            for relationship_tuple in [
                (
                    {"key": ["person-2", "person-3"], "other-key": ["person-3"]},
                    {"key": ["person-1", "person-3"], "other-key": ["person-3"]},
                ),
            ]
        ],
        # equality relationship
        *[
            (relationship_tuple, comparator, comparator == "equality")
            for comparator in [
                "one-way contains",
                "two-way contains",
                "either contains",
                "equality",
            ]
            for relationship_tuple in [
                (
                    {"key": ["person-3", "person-4"], "other-key": ["person-2"]},
                    {"key": ["person-3", "person-4"], "other-key": ["person-1"]},
                ),
            ]
        ],
    ],
)
def test_constraint_meet_criterion(
    relationship_params: tuple[dict[str, list[str]], dict[str, list[str]]],
    comparator: ComparatorType,
    expected_result: bool,
):
    person1 = MockPerson(
        name="person-1", relationships=relationship_params[0]
    ).get_model()
    person2 = MockPerson(
        name="person-2", relationships=relationship_params[1]
    ).get_model()

    constraint = MockConstraint(
        relationship_key="key",
        comparator=comparator,
    ).get_model()

    assert constraint.meet_criterion(person1, person2) == expected_result
