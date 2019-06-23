import subprocess
import os
import os.path
import sys
import tempfile
from tempfile import NamedTemporaryFile
from dataclasses import dataclass
from typing import Optional
import re

from production import utils

# This module lets you run your solutions against reference implementaiton
# It is future-proof in a sense that all the runs have "tag" argument
# that we will later be able to use to store results of solving in a database.
#
# Also, soon we will be able to run solvers directly using this runner.

def classify(result):
    if result.startswith("Success"):
        y = result.split("===")
        return ValidatorResult(time=int(y[1]), extra={})
    return ValidatorResult(time=None, extra=dict(error=result))

@dataclass
class ValidatorResult:
    time: Optional[int] # None on failures
    extra: dict # additional information, format is unstable


def do_run(tag: str, map: str, sol: str, boo: Optional[str]) -> ValidatorResult:
    fname = os.path.join(os.path.dirname(__file__), "run.js")
    if boo is None:
        result = subprocess.check_output(
            ("node", fname, '-m', map, '-s', sol),
            universal_newlines=True)
    else:
        result = subprocess.check_output(
            ("node", fname, '-m', map, '-s', sol, '-b', boo),
            universal_newlines=True)
    return classify(result.strip())


def puz(cond: str, descr: str) -> str:
    '''Return 'ok' or error message.'''

    assert (utils.project_root() / 'production' / 'golden' / 'node_modules').exists(), '''
    node_modules/ not found
    You probably need to run the following:
        cd production/golden
        npm install
    '''

    cond_name = tempfile.NamedTemporaryFile(delete=False).name
    with open(cond_name, 'w') as fout:
        fout.write(cond)

    descr_name = tempfile.NamedTemporaryFile(delete=False).name
    with open(descr_name, 'w') as fout:
        fout.write(descr)

    fname = os.path.join(os.path.dirname(__file__), "run.js")
    result = subprocess.check_output(
        ("node", fname, '-c', cond_name, '-d', descr_name),
        universal_newlines=True)

    os.remove(cond_name)
    os.remove(descr_name)

    result = result.strip()
    if result == 'Success===null':
        return 'ok'
    assert result != 'ok'
    return result


# UNTESTED ----------------------,
#                                v
def run(map: str, solution: str, boosters=None) -> ValidatorResult:
    assert (utils.project_root() / 'production' / 'golden' / 'node_modules').exists(), '''
    node_modules/ not found
    You probably need to run the following:
        cd production/golden
        npm install
    '''

    map_name = tempfile.NamedTemporaryFile(delete=False).name
    with open(map_name, 'w') as fout:
        fout.write(map)

    solution_name = tempfile.NamedTemporaryFile(delete=False).name
    with open(solution_name, 'w') as fout:
        fout.write(solution)

    booster_name = None
    if boosters is not None:
        booster_name = tempfile.NamedTemporaryFile(delete=False).name
        with open(booster_name, 'w') as fout:
            fout.write(booster)

    fname = os.path.join(os.path.dirname(__file__), "run.js")
    cmd = ["node", fname, '-m', map_name, '-s', solution_name]
    if boosters is not None:
        cmd += ['-b', booster_name]

    while True:
        result = subprocess.check_output(cmd, universal_newlines=True)
        result = result.strip()

        # This list was produced by running
        # SELECT id, extra->'validator'->'error', scent FROM solutions WHERE status='CHECK_FAIL'
        # and checking what looks like bullshit
        if result in [
            'Done uploading solution',
            'Done uploading task description',
            'Cannot check: some parts of the input are missing or malformed',
            ]:
            logging.warning(f'Retrying what looks like chrome flake ({result})')
            continue
        break

    m = re.match(r'Success===(\d+)$', result)
    if m:
        result = ValidatorResult(time=int(m.group(1)), extra={})
    else:
        result = ValidatorResult(time=None, extra=dict(error=result))

    os.remove(map_name)
    os.remove(solution_name)
    if boosters is not None:
        os.remove(booster_name)

    return result
