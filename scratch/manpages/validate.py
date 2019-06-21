import subprocess
import os
import os.path
import sys
import tempfile
from tempfile import NamedTemporaryFile
from dataclasses import dataclass
from typing import Optional

# This module lets you run your solutions against reference implementaiton
# It is future-proof in a sense that all the runs have "tag" argument
# that we will later be able to use to store results of solving in a database.
#
# Also, soon we will be able to run solvers directly using this runner.

def classify(result):
    if result.startswith("Success"):
        y = result.split("===")
        return ValidatorResult(time=int(y[1]), extra=y[0])
    return ValidatorResult(time=None, extra=result)

@dataclass
class ValidatorResult:
    time: Optional[int] # None on failures
    extra: dict # additional information, format is unstable

def do_run(tag: str, map: str, sol: str) -> ValidatorResult:
    fname = os.path.join(os.path.dirname(__file__), "run.js")
    result = subprocess.check_output(
        ("node", fname, '-m', map, '-s', sol),
        universal_newlines=True)
    return classify(result.strip())

def run(map: bytes, solution: bytes) -> ValidatorResult:
    map_name = tempfile.NamedTemporaryFile(delete=False).name
    with open(map_name, 'wb') as fout:
        fout.write(map)

    solution_name = tempfile.NamedTemporaryFile(delete=False).name
    with open(solution_name, 'wb') as fout:
        fout.write(solution)

    result = do_run("0.1.0-lgtn", str(map_name), str(solution_name))

    os.remove(map_name)
    os.remove(solution_name)
    return result

#TODO
#def solve(solver: TODOSolverClass, map: bytes, solution: bytes) -> ValidatorResult:
#   undefined

def main():
    result = do_run("0.1.0-lgtn", sys.argv[1], sys.argv[2])
    print(result)

if __name__ == "__main__":
    main()
