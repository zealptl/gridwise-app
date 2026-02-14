"""Transfer Service - Logic for tracking team transfers and penalties"""

from typing import List
from app.schemas.transfer import TransferChanges


class TransferService:
    """Business logic for transfer tracking and penalty calculation"""

    @staticmethod
    def calculate_changes(
        old_driver_ids: List[str],
        new_driver_ids: List[str],
        old_constructor_ids: List[str],
        new_constructor_ids: List[str],
    ) -> TransferChanges:
        """
        Calculate what entities were added/removed in a team update.

        Args:
            old_driver_ids: Current driver IDs in the team
            new_driver_ids: New driver IDs for the team
            old_constructor_ids: Current constructor IDs in the team
            new_constructor_ids: New constructor IDs for the team

        Returns:
            TransferChanges object with lists of added/removed entities
        """
        old_driver_set = set(old_driver_ids)
        new_driver_set = set(new_driver_ids)

        drivers_removed = list(old_driver_set - new_driver_set)
        drivers_added = list(new_driver_set - old_driver_set)

        old_constructor_set = set(old_constructor_ids)
        new_constructor_set = set(new_constructor_ids)

        constructors_removed = list(old_constructor_set - new_constructor_set)
        constructors_added = list(new_constructor_set - old_constructor_set)

        return TransferChanges(
            drivers_removed=drivers_removed,
            drivers_added=drivers_added,
            constructors_removed=constructors_removed,
            constructors_added=constructors_added,
        )

    @staticmethod
    def calculate_transfer_penalty(
        transfers_used: int, available_transfers: int
    ) -> int:
        """
        Calculate penalty points for excess transfers.

        Formula: max(0, transfers_used - available_transfers) * 10

        Args:
            transfers_used: Number of transfers made
            available_transfers: Number of free transfers available

        Returns:
            Penalty points (0 if within limit, 10 per excess transfer)

        Examples:
            - 1 transfer, 2 available = 0 penalty
            - 2 transfers, 2 available = 0 penalty
            - 3 transfers, 2 available = 10 penalty (1 excess)
            - 5 transfers, 2 available = 30 penalty (3 excess)
        """
        if transfers_used <= available_transfers:
            return 0

        excess = transfers_used - available_transfers
        penalty = excess * 10

        return penalty
