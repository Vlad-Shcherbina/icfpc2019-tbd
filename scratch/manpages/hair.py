import sys
from production.geom import *
from typing import Tuple

@dataclass
class Puzzle:
    block: int
    epoch: int
    testSize: int
    vertices: (int, int)
    manipulators: int
    fastWheels: int
    drills: int
    teleports: int
    cloning: int
    spawnPoints: int
    ioPoints: (List[Tuple[int, int]], List[Tuple[int, int]])

@dataclass
class Generator:
    x: int

def parseFromFile(x: str) -> Puzzle:
    y = ""
    with open(x, 'r') as fh:
        y = fh.read() 
    return parse(y)

def parse(x: str) -> Puzzle:
    s  = x.split('#')
    s0 = s[0].split(',') 
    return Puzzle(
        block=int(s0[0]),
        epoch=int(s0[1]),
        testSize=int(s0[2]),
        vertices=(int(s0[3]), int(s0[4])),
        manipulators=int(s0[5]),
        fastWheels=int(s0[6]),
        drills=int(s0[7]),
        teleports=int(s0[8]),
        cloning=int(s0[9]),
        spawnPoints=int(s0[10]),
        ioPoints=(toListOfPoints(s[1]), toListOfPoints(s[2]))
    )

def toListOfPoints(x: str) -> List[Tuple[int, int]]:
    y = []
    xx = x.split('),(')
    xx[0] = xx[0].strip('(')
    xx[-1] = xx[-1].strip(')')
    # yeah, yeah, I know
    for v in xx:
        z = v.split(',')
        y.append((int(z[0]), int(z[1])))
    return y

def main():
    result = parseFromFile(sys.argv[1])
    print(result)

if __name__ == "__main__":
    main()
