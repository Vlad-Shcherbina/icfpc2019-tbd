from .utils import get_problem_raw

def test_get_problem_raw():
    assert get_problem_raw(1) == '(0,0),(6,0),(6,1),(8,1),(8,2),(6,2),(6,3),(0,3)#(0,0)##'
