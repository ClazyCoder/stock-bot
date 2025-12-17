from typing import List, Generator, TypeVar

T = TypeVar('T')


def chunk_list(lst: List[T], n: int) -> Generator[List[T], None, None]:
    """
    Chunk a list into smaller lists of size n.
    Args:
        lst (List[T]): The list to chunk.
        n (int): The size of the chunks. Must be greater than 0.
    Returns:
        Generator[List[T], None, None]: A generator of lists.
    Raises:
        ValueError: If n is less than or equal to 0.
    """
    if n <= 0:
        raise ValueError(f"Chunk size 'n' must be greater than 0, got {n}")
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
