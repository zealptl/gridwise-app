"""Unit tests for TransferService"""

import pytest
from app.services.transfer_service import TransferService
from app.schemas.transfer import TransferChanges


class TestCalculateChanges:
    """Test the calculate_changes method"""

    def test_no_changes(self):
        """Test when no changes are made to the team"""
        old_drivers = ["d1", "d2", "d3", "d4", "d5"]
        new_drivers = ["d1", "d2", "d3", "d4", "d5"]
        old_constructors = ["c1", "c2"]
        new_constructors = ["c1", "c2"]

        changes = TransferService.calculate_changes(
            old_drivers, new_drivers, old_constructors, new_constructors
        )

        assert changes.drivers_removed == []
        assert changes.drivers_added == []
        assert changes.constructors_removed == []
        assert changes.constructors_added == []
        assert changes.get_transfer_count() == 0

    def test_single_driver_swap(self):
        """Test swapping one driver (E for F)"""
        old_drivers = ["d1", "d2", "d3", "d4", "d5"]
        new_drivers = ["d1", "d2", "d3", "d4", "d6"]
        old_constructors = ["c1", "c2"]
        new_constructors = ["c1", "c2"]

        changes = TransferService.calculate_changes(
            old_drivers, new_drivers, old_constructors, new_constructors
        )

        assert set(changes.drivers_removed) == {"d5"}
        assert set(changes.drivers_added) == {"d6"}
        assert changes.constructors_removed == []
        assert changes.constructors_added == []
        assert changes.get_transfer_count() == 1

    def test_multiple_driver_swaps(self):
        """Test swapping multiple drivers"""
        old_drivers = ["d1", "d2", "d3", "d4", "d5"]
        new_drivers = ["d1", "d2", "d3", "d6", "d7"]
        old_constructors = ["c1", "c2"]
        new_constructors = ["c1", "c2"]

        changes = TransferService.calculate_changes(
            old_drivers, new_drivers, old_constructors, new_constructors
        )

        assert set(changes.drivers_removed) == {"d4", "d5"}
        assert set(changes.drivers_added) == {"d6", "d7"}
        assert changes.constructors_removed == []
        assert changes.constructors_added == []
        assert changes.get_transfer_count() == 2

    def test_single_constructor_swap(self):
        """Test swapping one constructor"""
        old_drivers = ["d1", "d2", "d3", "d4", "d5"]
        new_drivers = ["d1", "d2", "d3", "d4", "d5"]
        old_constructors = ["c1", "c2"]
        new_constructors = ["c1", "c3"]

        changes = TransferService.calculate_changes(
            old_drivers, new_drivers, old_constructors, new_constructors
        )

        assert changes.drivers_removed == []
        assert changes.drivers_added == []
        assert set(changes.constructors_removed) == {"c2"}
        assert set(changes.constructors_added) == {"c3"}
        assert changes.get_transfer_count() == 1

    def test_driver_and_constructor_swaps(self):
        """Test swapping both drivers and constructors"""
        old_drivers = ["d1", "d2", "d3", "d4", "d5"]
        new_drivers = ["d1", "d2", "d3", "d4", "d6"]
        old_constructors = ["c1", "c2"]
        new_constructors = ["c1", "c3"]

        changes = TransferService.calculate_changes(
            old_drivers, new_drivers, old_constructors, new_constructors
        )

        assert set(changes.drivers_removed) == {"d5"}
        assert set(changes.drivers_added) == {"d6"}
        assert set(changes.constructors_removed) == {"c2"}
        assert set(changes.constructors_added) == {"c3"}
        assert changes.get_transfer_count() == 2  # 1 driver + 1 constructor

    def test_complete_team_overhaul(self):
        """Test replacing all drivers and constructors"""
        old_drivers = ["d1", "d2", "d3", "d4", "d5"]
        new_drivers = ["d6", "d7", "d8", "d9", "d10"]
        old_constructors = ["c1", "c2"]
        new_constructors = ["c3", "c4"]

        changes = TransferService.calculate_changes(
            old_drivers, new_drivers, old_constructors, new_constructors
        )

        assert set(changes.drivers_removed) == {"d1", "d2", "d3", "d4", "d5"}
        assert set(changes.drivers_added) == {"d6", "d7", "d8", "d9", "d10"}
        assert set(changes.constructors_removed) == {"c1", "c2"}
        assert set(changes.constructors_added) == {"c3", "c4"}
        assert changes.get_transfer_count() == 7  # 5 drivers + 2 constructors


class TestCalculateTransferPenalty:
    """Test the calculate_transfer_penalty method"""

    def test_no_transfers_no_penalty(self):
        """Test 0 transfers with 2 available"""
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=0, available_transfers=2
        )
        assert penalty == 0

    def test_one_transfer_no_penalty(self):
        """Test 1 transfer with 2 available (within limit)"""
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=1, available_transfers=2
        )
        assert penalty == 0

    def test_two_transfers_no_penalty(self):
        """Test 2 transfers with 2 available (at limit)"""
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=2, available_transfers=2
        )
        assert penalty == 0

    def test_three_transfers_one_excess(self):
        """Test 3 transfers with 2 available (1 excess = 10 penalty)"""
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=3, available_transfers=2
        )
        assert penalty == 10

    def test_four_transfers_two_excess(self):
        """Test 4 transfers with 2 available (2 excess = 20 penalty)"""
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=4, available_transfers=2
        )
        assert penalty == 20

    def test_five_transfers_three_excess(self):
        """Test 5 transfers with 2 available (3 excess = 30 penalty)"""
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=5, available_transfers=2
        )
        assert penalty == 30

    def test_wildcard_scenario(self):
        """Test wildcard scenario (7 transfers = 5 excess = 50 penalty)"""
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=7, available_transfers=2
        )
        assert penalty == 50

    def test_with_three_available_transfers(self):
        """Test with 3 available transfers (carryover from previous race)"""
        # 3 transfers with 3 available = no penalty
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=3, available_transfers=3
        )
        assert penalty == 0

        # 4 transfers with 3 available = 10 penalty
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=4, available_transfers=3
        )
        assert penalty == 10

    def test_edge_case_zero_available(self):
        """Test edge case with 0 available transfers"""
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=2, available_transfers=0
        )
        assert penalty == 20
