from .protocol import SearchSpaceReducer as SearchSpaceReducer
from .techniques.dual_pathway_pruning import (
    DualPathwayPruner as DualPathwayPruner,
)

__all__ = [
    "DualPathwayPruner",
    "SearchSpaceReducer",
]
