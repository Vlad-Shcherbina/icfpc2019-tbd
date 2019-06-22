from pathlib import Path

from typing import List
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



def test_one_bot_game():
    # simple moves
    actions = Action.parse('WWWWWWWWWDDSSSSSSSSSDDDDWWWWWWWWWAASSDDDDDWWAZZSSSSSSSSS')
    run_one_bot_game(actions)

    # turns
    actions = Action.parse('DQWWWWWWWWEDDEWDDDDDADQSSSSSSSSEAAAAAEEWWWWWWEDDDESSSS')
    run_one_bot_game(actions)

    # building manips
    actions = Action.parse('WB(0,1)WWWWWWWDDSSSSSSSADDDDDWWWWWWAAWWDDDDSSSSSSSSA')
    run_one_bot_game(actions)

    # teleport
    actions = Action.parse('DWDDDDDDDWWAAWWDDWWAAAARASSSSAAASSWWWWWWWWDDSSSST(4,7)WWDDDD')
    run_one_bot_game(actions)

def test_cloning_game():
    act_str = 'DWADDDDDDDDWAASAAAAEB(1,0)AWWWWAWWWWCDDDDDDDDSSSAZZSFSDWA#CSSSEDDWAASSSSSDDWWW#SDDDDSDDSSSZZSSSAA'.split('#')
    actionlist = [Action.parse(s) for s in act_str]
    run_cloned_game(actionlist)


if __name__ == '__main__':
    utils.testmod()
