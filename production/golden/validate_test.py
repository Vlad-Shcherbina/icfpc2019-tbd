from production import utils
from production.golden.validate import run, do_run, puz
from production.golden.validate import ValidatorResult
import os


'''
def test_big_solution():
    task = (utils.project_root() / 'production' / 'golden' / '300.desc').read_text()
    sol = (utils.project_root() / 'production' / 'golden' / 'sol-526.sol').read_text()
    result = run(task, sol)
    print(result)
    assert result.time == 44556
'''

def test_valid_puzzle():
    puzzle = (utils.project_root() / 'tasks' / 'chain-puzzle-examples' / 'puzzle.cond').read_text()
    task = (utils.project_root() / 'tasks' / 'chain-puzzle-examples' / 'task.desc').read_text()
    result = puz(puzzle, task)
    assert result == 'ok', result


def test_invalid_puzzle():
    cond = (utils.project_root() / 'production' / 'golden' / 'puzzle.cond').read_text()
    desc = (utils.project_root() / 'production' / 'golden' / 'broken.desc').read_text()
    result = puz(cond, desc)
    print(result)
    assert result != 'ok'


def test_valid_solution():
    task = (utils.project_root() / 'tasks' / 'part-1-examples' / 'example-01.desc').read_text()
    sol = (utils.project_root() / 'tasks' / 'part-1-examples' / 'example-01-1.sol').read_text()
    result = run(task, sol)
    print(result)
    assert result.time == 48


def test_invalid_solution():
    task = (utils.project_root() / 'tasks' / 'part-1-examples' / 'example-01.desc').read_text()
    sol = 'WSAD'
    result = run(task, sol)
    print(result)
    assert result.time is None


if __name__ == '__main__':
    utils.testmod()
