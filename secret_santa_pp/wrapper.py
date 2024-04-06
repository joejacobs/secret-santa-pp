from typing import TYPE_CHECKING, Generic, TypeVar

from networkx import DiGraph as nxDiGraph

T = TypeVar("T")


# networkx graphs are not properly typed. This is a workaround so that the
# linter works as expected.
if TYPE_CHECKING:

    class _DiGraph(nxDiGraph[T]):  # pragma: no cover
        pass
else:

    class _DiGraph(Generic[T], nxDiGraph):
        pass


class DiGraph(_DiGraph[T]):
    pass
