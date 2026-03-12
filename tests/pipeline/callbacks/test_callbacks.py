from pathlib import Path
from cxview import cxview

def test_callbacks():
    flags = [
        '-x', 'c++',
        '-std=c++17',
        '-I./src'
    ]

    cxview(Path("callbacks.h"), flags=flags)

if __name__ == "__main__":
    test_callbacks()