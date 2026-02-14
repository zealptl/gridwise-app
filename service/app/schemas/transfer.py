"""Transfer Request/Response Schemas"""

from typing import List
from pydantic import BaseModel


class Change(BaseModel):
    """Individual change in a team update (driver/constructor in/out)"""

    type: str  # "driver_out", "driver_in", "constructor_out", "constructor_in"
    entity_id: str
    entity_name: str
    price: float


class TransferChanges(BaseModel):
    """Track what changed in a team update"""

    drivers_removed: List[str] = []
    drivers_added: List[str] = []
    constructors_removed: List[str] = []
    constructors_added: List[str] = []

    def get_transfer_count(self) -> int:
        """
        Calculate the number of transfers used.
        Each driver/constructor swap counts as 1 transfer.
        DRS Boost changes do not count.
        """
        return len(self.drivers_removed) + len(self.constructors_removed)
