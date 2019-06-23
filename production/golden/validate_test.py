from production import utils
from production.golden.validate import run, do_run
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


exampleDesc = "(0,0),(10,0),(10,10),(0,10)#(0,0)#(4,2),(6,2),(6,7),(4,7);(5,8),(6,8),(6,9),(5,9)#B(0,1);B(1,1);F(0,2);F(1,2);L(0,3);X(0,9)\n"
exampleSol1 = "WDWB(1,2)DSQDB(-3,1)DDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW\n"
exampleWrg1 = "DWDSQDDDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW\n"
exampleWrg2 = "DWB(1,2)DSQDB(-3,1)DDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW\n"
exampleWrg3 = "WDWB(1,2)DSQDB(-4,1)DDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW\n"

# NB! Trailing \n is optional!
exampleNnn1 = "WDWB(1,2)DSQDB(-3,1)DDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW"

exampleDescFile = os.path.join(os.path.dirname(__file__), "icfpcontest2019.github.io/download/example-01.desc")
exampleSol1File = os.path.join(os.path.dirname(__file__), "icfpcontest2019.github.io/download/example-01-1.sol")

'''
def test_suite():
    assert run(exampleDesc, exampleSol1) == ValidatorResult(time=48, extra={})

    # NB! Trailing \n is optional!
    assert run(exampleDesc, exampleNnn1) == ValidatorResult(time=48, extra={})

    assert run(exampleDesc, exampleWrg1).time == None
    assert run(exampleDesc, exampleWrg2).time == None
    assert run(exampleDesc, exampleWrg3).time == None
    assert do_run("test", exampleDescFile, exampleSol1File) == run(exampleDesc, exampleSol1)

if __name__ == "__main__":
    main()
'''
