from typing import TYPE_CHECKING, Generic, TypeVar

from networkx import DiGraph as nxDiGraph

T = TypeVar("T")


if TYPE_CHECKING:

    class _DiGraph(nxDiGraph[T]):
        pass
else:

    class _DiGraph(Generic[T], nxDiGraph):
        pass


class DiGraph(_DiGraph[T]):
    pass
