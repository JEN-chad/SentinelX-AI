"""SentinelX AI - Chunked CSV Reader

Reads CSV flow records iteratively in bounded chunks to avoid memory bottlenecks.
"""

import csv
from pathlib import Path
from typing import Dict, Generator, List, Union


def read_csv_in_chunks(
    file_path: Union[str, Path],
    chunk_size: int = 500,
) -> Generator[List[Dict[str, str]], None, None]:
    """Yield records in batches from a CSV file.
    
    Args:
        file_path: Path to the CSV file.
        chunk_size: Max rows to yield in each batch.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found at '{path}'")

    with open(path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        batch: List[Dict[str, str]] = []
        for row in reader:
            batch.append(row)
            if len(batch) >= chunk_size:
                yield batch
                batch = []
        if batch:
            yield batch
