import os
import os.path

from production.golden.validate import run
from production.golden.validate import do_run
from production.golden.validate import ValidatorResult

exampleDesc = "(0,0),(10,0),(10,10),(0,10)#(0,0)#(4,2),(6,2),(6,7),(4,7);(5,8),(6,8),(6,9),(5,9)#B(0,1);B(1,1);F(0,2);F(1,2);L(0,3);X(0,9)\n".encode('utf-8')
exampleSol1 = "WDWB(1,2)DSQDB(-3,1)DDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW\n".encode('utf-8')
exampleWrg1 = "DWDSQDDDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW\n".encode('utf-8')
exampleWrg2 = "DWB(1,2)DSQDB(-3,1)DDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW\n".encode('utf-8')
exampleWrg3 = "WDWB(1,2)DSQDB(-4,1)DDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW\n".encode('utf-8')

# NB! Trailing \n is optional!
exampleNnn1 = "WDWB(1,2)DSQDB(-3,1)DDDWWWWWWWSSEDSSDWWESSSSSAAAAAQQWWWWWWW".encode('utf-8')

exampleDescFile = os.path.join(os.path.dirname(__file__), "icfpcontest2019.github.io/download/example-01.desc")
exampleSol1File = os.path.join(os.path.dirname(__file__), "icfpcontest2019.github.io/download/example-01-1.sol")

def main():
    assert run(exampleDesc, exampleSol1) == ValidatorResult(time=48, extra='Success')

    # NB! Trailing \n is optional!
    assert run(exampleDesc, exampleNnn1) == ValidatorResult(time=48, extra='Success')

    assert run(exampleDesc, exampleWrg1).time == None
    assert run(exampleDesc, exampleWrg2).time == None
    assert run(exampleDesc, exampleWrg3).time == None
    assert do_run("test", exampleDescFile, exampleSol1File) == run(exampleDesc, exampleSol1)

if __name__ == "__main__":
    main()
