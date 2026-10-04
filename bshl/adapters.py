"""Provider boundary for frozen daily snapshots; no live provider is bundled."""
from dataclasses import dataclass
from typing import Protocol
from .market import Dataset, as_of_slice, load_dataset, parse_timestamp, validate_dataset
from data.contracts import validate_symbol


class MarketDataAdapter(Protocol):
    def snapshot(self, symbol: str, as_of) -> Dataset:
        """Return declared provenance or raise; never silently substitute mock data."""
        ...


@dataclass(frozen=True)
class CSVSnapshotAdapter:
    csv_path: str
    metadata_path: str

    def snapshot(self, symbol, as_of):
        dataset = load_dataset(self.csv_path, self.metadata_path)
        if dataset.symbol != symbol:
            raise ValueError("Requested symbol does not match CSV identity")
        return as_of_slice(dataset, parse_timestamp(as_of))


def validated_snapshot(adapter: MarketDataAdapter, symbol, as_of, *, allow_mock=False):
    validate_symbol(symbol)
    if type(allow_mock) is not bool:
        raise ValueError("allow_mock must be a boolean")
    cutoff = parse_timestamp(as_of)
    dataset = adapter.snapshot(symbol, cutoff)
    validate_dataset(dataset)
    if dataset.symbol != symbol:
        raise ValueError("Provider identity mismatch")
    if dataset.is_mock and not allow_mock:
        raise ValueError("Mock snapshot requires explicit allow_mock=True")
    visible = as_of_slice(dataset, cutoff)
    if not visible.bars:
        raise ValueError("No snapshot bars were available at the decision time")
    return visible
