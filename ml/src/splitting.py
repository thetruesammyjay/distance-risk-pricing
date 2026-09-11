from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass

from ml.src.contracts import RiskRecord


@dataclass(frozen=True, slots=True)
class GroupIndexSplit:
    train_indices: tuple[int, ...]
    test_indices: tuple[int, ...]
    train_groups: frozenset[str]
    test_groups: frozenset[str]


@dataclass(frozen=True, slots=True)
class DatasetSplit:
    train: tuple[RiskRecord, ...]
    test: tuple[RiskRecord, ...]

    @property
    def train_groups(self) -> frozenset[str]:
        return frozenset(record.respondent_id for record in self.train)

    @property
    def test_groups(self) -> frozenset[str]:
        return frozenset(record.respondent_id for record in self.test)


def grouped_train_test_indices(
    groups: Sequence[str], *, test_size: float = 0.2, seed: int = 42
) -> GroupIndexSplit:
    """Return respondent-grouped indices for any long-format dataset."""

    if not groups:
        raise ValueError("at least one record is required")
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")
    unique_groups = sorted(set(groups))
    if len(unique_groups) < 2:
        raise ValueError("at least two respondent groups are required")
    shuffled = unique_groups.copy()
    random.Random(seed).shuffle(shuffled)
    test_group_count = max(1, math.ceil(len(unique_groups) * test_size))
    test_groups = frozenset(shuffled[:test_group_count])
    train_indices = tuple(index for index, group in enumerate(groups) if group not in test_groups)
    test_indices = tuple(index for index, group in enumerate(groups) if group in test_groups)
    if not train_indices or not test_indices:
        raise ValueError("split must contain both train and test records")
    return GroupIndexSplit(
        train_indices=train_indices,
        test_indices=test_indices,
        train_groups=frozenset(unique_groups) - test_groups,
        test_groups=test_groups,
    )


def grouped_train_test_split(
    records: Sequence[RiskRecord], *, test_size: float = 0.2, seed: int = 42
) -> DatasetSplit:
    """Split by respondent, never by individual observation."""

    index_split = grouped_train_test_indices(
        [record.respondent_id for record in records], test_size=test_size, seed=seed
    )
    train = tuple(records[index] for index in index_split.train_indices)
    test = tuple(records[index] for index in index_split.test_indices)
    return DatasetSplit(train, test)


def assert_no_group_overlap(split: DatasetSplit | GroupIndexSplit) -> None:
    overlap = split.train_groups & split.test_groups
    if overlap:
        raise AssertionError(f"respondent groups overlap between partitions: {sorted(overlap)}")