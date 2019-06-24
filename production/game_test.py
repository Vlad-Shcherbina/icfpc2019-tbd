from pathlib import Path
from typing import List

import pytest

from production import utils
from production.golden import validate
from production.data_formats import Task, GridTask, Action, compose_actions
from production.game import Game, InvalidActionException

def run_one_bot_game(actions: List[Action]):
    task_data = Path(utils.project_root() / 'tasks' / 'part-0-mock' / 'prob-2003.desc').read_text()
    task = GridTask(Task.parse(task_data))
    game = Game(task)
    for a in actions:
        game.apply_action(a)

    solution = compose_actions(game.get_actions())
    expected_score = game.finished()
    er = validate.run(task_data, solution)

    assert er.time is not None
    assert er.time == expected_score


def run_cloned_game(actions: List[List[Action]]):
    task_data = Path(utils.project_root() / 'tasks' / 'part-0-mock' / 'prob-2003.desc').read_text()
    task = GridTask(Task.parse(task_data))
    game = Game(task)

    indices = [0] * len(actions)
    current = 0
    while not game.finished():
        if current == 0:
            botcount = len(game.bots)
        i = indices[current]
        game.apply_action(actions[current][i], current)
        indices[current] += 1
        current = (current + 1) % botcount

    solution = compose_actions(game.get_actions())
    expected_score = game.finished()
    er = validate.run(task_data, solution)

    assert er.time is not None
    assert er.time == expected_score


def run_for_errors(actions: List[Action]):
    task_data = Path(utils.project_root() / 'tasks' / 'part-0-mock' / 'prob-2003.desc').read_text()
    task = GridTask(Task.parse(task_data))
    game = Game(task)
    try:
        for a in actions:
            game.apply_action(a)
    except InvalidActionException:
        return
    else:
        assert False



def test_wheel_timer():
    task_data = Path(utils.project_root() / 'tasks' / 'part-0-mock' / 'wheels.desc').read_text()
    task = GridTask(Task.parse(task_data))

    actionlist = ('QQDD' + 
                     'F' +
                     'ZZZZZZZZZZZZZZZZZZZZ' +
                     'F' +
                     'ZZZZZZZZZZZZZZZZZZZZ' + 
                     'ZZZZZZZZZ' +
                     'ZZZZZZZZZZZZZZZZZZZZ' +
                     'ZZZZZZZZZZZZZZZZZZZZ' +
                     'ZZZZZZZZZZ' + 
                     'D')

    game = Game(task)
    for a in actionlist:
        game.apply_action(Action.simple(a))

    solution = compose_actions(game.get_actions())
    expected_score = game.finished()
    assert expected_score is None

    game = Game(task)
    for a in actionlist:
        game.apply_action(Action.simple(a))
    game.apply_action(Action.WSAD('D'))

    solution = compose_actions(game.get_actions())
    expected_score = game.finished()
    er = validate.run(task_data, solution)

    assert er.time is not None
    assert er.time == expected_score




def test_simple_moves():
    actions = Action.parse('WWWWWWWWWDDSSSSSSSSSDDDDWWWWWWWWWAASSDDDDDWWAZZSSSSSSSSS')
    run_one_bot_game(actions)

def test_turns():
    actions = Action.parse('DQWWWWWWWWEDDEWDDDDDADQSSSSSSSSEAAAAAEEWWWWWWEDDDESSSS')
    run_one_bot_game(actions)

def test_building_manips():
    actions = Action.parse('WB(0,1)WWWWWWWDDSSSSSSSADDDDDWWWWWWAAWWDDDDSSSSSSSSA')
    run_one_bot_game(actions)

def test_teleport():
    actions = Action.parse('DWDDDDDDDWWAAWWDDWWAAAARASSSSAAASSWWWWWWWWDDSSSST(4,7)WWDDDD')
    run_one_bot_game(actions)

def test_drill_and_wheels():
    actions = Action.parse('WWWFDDLWAQQWWDDSSAWDDQWQQSSSSQAAEEDDDQWWWW')
    run_one_bot_game(actions)


def test_clones_game():
    act_str = 'DWADDDDDDDDWAASAAAAEB(1,0)AWWWWAWWWWCDDDDDDDDSSSAZZSFSDWA#CSSSEDDWAASSSSSDDWWW#SDDDDSDDSSSZZSSSAA'.split('#')
    actionlist = [Action.parse(s) for s in act_str]
    run_cloned_game(actionlist)


@pytest.mark.parametrize('actions',[
    pytest.param('A', id='out of bound'),
    pytest.param('WWWWWWWWWWWWWWW', id='out of bound 2'),
    pytest.param('WWWSSSSSS', id='to obstacle'),
    pytest.param('WWFF', id='inventory is empty - only one wheel'),
    pytest.param('DDDDDDDDWC', id='cloning out of spot'),
    pytest.param('DDDDDDDDWWWWWRSST(1,1)', id='teleporting to wrong place'),
    pytest.param('WB(1,1)', id='manipulators'),
    pytest.param('WB(3,1)', id='manipulators 2'),
])
def test_error(actions):
    actions = Action.parse(actions)
    run_for_errors(actions)

def test_clone_errors():
    actionlist = [Action.parse('DDDDDDDDAAAAAAWWWWWWWWWAACSSSSSSSS'),
                  Action.parse('DDDDDLDZ')]
    try:
        run_cloned_game(actionlist)
    except InvalidActionException:
        return
    else:
        assert False




if __name__ == '__main__':
    utils.testmod()
