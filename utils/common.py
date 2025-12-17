from typing import List, Generator, TypeVar

T = TypeVar('T')


def chunk_list(lst: List[T], n: int) -> Generator[List[T], None, None]:
    """
    Chunk a list into smaller lists of size n.
    Args:
        lst (List[T]): The list to chunk.
        n (int): The size of the chunks.
    Returns:
        Generator[List[T], None, None]: A generator of lists.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
