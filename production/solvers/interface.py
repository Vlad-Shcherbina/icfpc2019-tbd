from dataclasses import dataclass, field
from typing import Union, List, Optional


@dataclass
class Pass:
    pass


@dataclass
class Fail:
    pass


@dataclass
class SolverResult:
    data: Union[str, Pass, Fail]

    expected_score: Optional[int]
    # None if Pass or Fail or if your solver doesn't know what score it gets.

    extra: dict = field(default_factory=dict)
    # any additional informaion (stats, errors, comments)
    # should be json-encodable


class Solver:
    def __init__(self, args: List[str]):
        '''
        args come from the command line, could be used as tuning parameters
        or something
        '''
        pass

    def scent(self) -> str:
        '''Solver identifier to avoid redundant reruns.

        Use something like "My solver 1.0" and bump version when
        the solver changed significantly and you want to rerun on all tasks.
        The solver will not run again on the tasks where there were
        attempts (no matter successful or not) with the same scent.

        Args can be included in the scent if they affect significantly
        how the solver works.
        '''
        raise NotImplementedError()

    def solve(self, task: str) -> SolverResult:
        '''
        Return SolverData(
            data=compose_actions(actions),
            expected_score=42,
            extra={...})
        on success.

        Return SolverData(Pass(), extra={...}) if the solver predicatably failed
        (ran into a case that is not supported by design).
        Ideally try to avoid it.

        Return SolverData(Fail(), extra={...}) if the solver failed
        in an unintended way worth investigating and fixing.
        Don't bother catching exceptions in your solver,
        solver runner will handle that.
        '''
        raise NotImplementedError()
