from pathlib import Path
from zipfile import ZipFile

def project_root() -> Path:
    return (Path(__file__)/'..'/'..').resolve()


def get_problem_raw(n):
    'Returns the raw contents of the problem description. n is 1-based!'
    # will be extended as we get more tasks

    if 1 <= n <= 150:
        part = 'part-1-initial'
    elif 151 <= n <= 220:
        part = 'part-2-teleports'
    elif 221 <= n <= 300:
        part = 'part-3-clones'
    elif n >= 1000:
        return get_mock_problem(n)
    else:
        assert False, n

    with ZipFile(project_root() / 'tasks' / f'{part}.zip') as z:
        with z.open(f'prob-{n:03d}.desc', 'r') as fin:
            return fin.read().decode()


def get_mock_problem(n):
    with Path(project_root() / 'tasks' / 'part-0-mock' / f'prob-{n}.desc') as fin:
        return fin.read_text()



def testmod():
    '''Black magic.

    Call it from under "if name == '__main__'" from test modules.
    Then running such test module as a script will run all tests in this module.
    '''
    import pytest
    import inspect
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    pytest.main(['-vx', mod.__file__])
