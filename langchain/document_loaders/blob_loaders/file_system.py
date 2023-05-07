"""Use to load blobs from the local file system."""
from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

from langchain.document_loaders.blob_loaders.schema import Blob, BlobLoader

# PUBLIC API


class FileSystemBlobLoader(BlobLoader):
    """Blob loader for the local file system.

    Example:

    .. code-block:: python

        from langchain.document_loaders.blob_loaders import FileSystemBlobLoader
        loader = FileSystemBlobLoader("/path/to/directory")
        for blob in loader.yield_blobs():
            print(blob)
    """

    def __init__(
        self,
        path: Union[str, Path],
        *,
        glob: str = "**/[!.]*",
        suffixes: Optional[Sequence[str]] = None,
        show_progress: bool = False,
    ) -> None:
        """Initialize with path to directory and how to glob over it.

        Args:
            path: Path to directory to load from
            glob: Glob pattern relative to the specified path
                  by default set to pick up all non-hidden files
            suffixes: Provide to keep only files with these suffixes
                      Useful when wanting to keep files with different suffixes
                      Suffixes must include the dot, e.g. ".txt"
            show_progress: If true, will show a progress bar as the files are loaded.
                           This forces an iteration through all matching files
                           to count them prior to loading them.

        Examples:

        ... code-block:: python

            # Recursively load all text files in a directory.
            loader = FileSystemBlobLoader("/path/to/directory", glob="**/*.txt")

            # Recursively load all non-hidden files in a directory.
            loader = FileSystemBlobLoader("/path/to/directory", glob="**/[!.]*")

            # Load all files in a directory without recursion.
            loader = FileSystemBlobLoader("/path/to/directory", glob="*")
        """
        if isinstance(path, Path):
            _path = path
        elif isinstance(path, str):
            _path = Path(path)
        else:
            raise TypeError(f"Expected str or Path, got {type(path)}")

        self.path = _path
        self.glob = glob
        self.suffixes = set(suffixes or [])
        self.show_progress = show_progress

    def yield_blobs(
        self,
    ) -> Iterable[Blob]:
        """Yield blobs that match the requested pattern."""
        if self.show_progress:
            from tqdm.auto import tqdm

            with tqdm(total=self.count_matching_files()) as progress_bar:
                for path in self._yield_paths():
                    yield Blob.from_path(path)
                    progress_bar.update(1)
        else:
            yield from (Blob.from_path(path) for path in self._yield_paths())

    def _yield_paths(self) -> Iterable[Path]:
        """Yield paths that match the requested pattern."""
        paths = self.path.glob(self.glob)
        for path in paths:
            if path.is_file():
                if self.suffixes and path.suffix not in self.suffixes:
                    continue
                yield path

    def count_matching_files(self) -> int:
        """Count files that match the pattern without loading them."""
        # Carry out a full iteration to count the files without
        # materializing anything expensive in memory.
        num = 0
        for _ in self._yield_paths():
            num += 1
        return num
