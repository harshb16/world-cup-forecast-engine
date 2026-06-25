"""Deterministic child seed generation for parallel simulation batches."""

from __future__ import annotations


class SeedSequence:
    """Derive independent child seeds from one master seed."""

    def __init__(self, master_seed: int) -> None:
        self.master_seed = master_seed & 0xFFFFFFFF

    def child_seed(self, batch_index: int, simulation_index: int) -> int:
        mixed = (
            self.master_seed
            ^ (batch_index * 1_000_003)
            ^ (simulation_index * 9_999_983)
        ) & 0xFFFFFFFF
        return int(mixed % (2**31 - 1))
