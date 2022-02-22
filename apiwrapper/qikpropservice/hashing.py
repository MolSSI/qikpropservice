"""
Hashing utility for incoming files
"""

__all__ = ["generate_checksum_file", "DEFAULT_HASH_FUNCTION"]

import hashlib
from pathlib import Path
from typing import Union

DEFAULT_HASH_FUNCTION = "sha1"


def generate_checksum_file(filepath: Union[Path, str], chunksize=4096, hash_function=DEFAULT_HASH_FUNCTION):
    cummulative_hash = getattr(hashlib, hash_function)()  # Setup up blank checksum
    with open(filepath, "rb") as file:
        # Process file in chunks
        for byte_block in iter(lambda: file.read(chunksize), b""):
            cummulative_hash.update(byte_block)
    return cummulative_hash.hexdigest()
