from pathlib import Path

def project_root() -> Path:
    return (Path(__file__)/'..'/'..').resolve()


def get_problem_raw(n):
    'Returns the raw contents of the problem description. n is 1-based!'
    # will be extended as we get more tasks
    fname =  project_root() / 'tasks' / 'part-1-initial' / f'prob-{n:03d}.desc'
    return fname.read_text()


def testmod():
    'Black magic'
    import pytest
    import inspect
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    pytest.main(['-vx', mod.__file__])

