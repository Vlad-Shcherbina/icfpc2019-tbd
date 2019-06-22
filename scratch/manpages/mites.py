import sys

from production.data_formats import Puzzle, Task
from production.geom import Pt
from typing import List, Optional

'''
StalaCtite grows down from a Ceiling
StalaGmite grows up from the Ground.
'''

def solve(puz: Puzzle) -> Task:
    vertices = [Pt(0, 0),
                Pt(puz.size, 0),
                Pt(puz.size, puz.size),
                Pt(0, puz.size)]
    include   = puz.include
    omit      = puz.omit
    tentacles = []
    for p in omit:
        mit = stalagmitable(p, include)
        tit = stalactitable(p, include, puz.size)
        if mit and tit:
            # Sometimes there are several Os in a row,
            # we want to be a little smarter here not to
            # cut the map in two!
            if mit < tit:
                mkStalagmite(vertices, p)
                continue
            else:
                mkStalactite(vertices, p)
                continue
        if mit:
            mkStalagmite(vertices, p)
            continue
        if tit:
            mkStalactite(vertices, p)
            continue
        # If it came to this, it means that point `p` is blocked by
        # a must-include point both from the top and from the bottom
        # your goal is to implemet an algorithm that will move around
        # must-include obstacles and touch the target must-omit point
        # with the wall.
        tentacles.append(p)
    if len(tentacles) > 0:
        assert False, ("Points", str(tentacles), " are blocked.")
    return Task(border=vertices, start=Pt(0,149), obstacles=[], boosters=[])

def mkStalactite(vertices, p):
    return

def mkStalagmite(vertices, p):
    #print(['vs', vertices, 'point', p])
    vslen = len(vertices)
    for k, v in enumerate(vertices):
        #if p.x == 4 and p.y == 40:
        #    print(Task(vertices, Pt(2,2), [], []))
        #print(['k', k, 'v', v])
        if k >= vslen:
            break
        cx = v.x
        cy = v.y
        nx = vertices[k+1].x
        ny = vertices[k+1].y
        #print(['p.x', p.x, 'cx', cx, 'nx', nx])
        if cx <= p.x and nx > p.x:
            # If current vertex is positioned not on the left of target point
            # and the next vertex is positioned on the left of target point
            # it means that we have arrived to a flat platform on which
            # we're going to grow our stalagmite.
            if (cy > p.y):
                #print("Job's done")
                # Our job is already done, the point is in the wall
                break
            _k = k
            if (cx == p.x): # Platform starts where we need to grow stalagmite
                #print("Platform starts")
                vertices[_k] = Pt(v.x, p.y + 1)
            else: # We have to insert two vertices to start stalagmite
                #print("Insert two at the beginning")
                vertices.insert(_k + 1, Pt(p.x, cy))
                vertices.insert(_k + 2, Pt(p.x, p.y + 1))
                _k = _k + 2
            if (nx == p.x + 1):
                #print("Platform ends")
                vertices[_k + 1] = Pt(vertices[_k + 1].x, p.y + 1)
            else:
                #print("Insert two at the end")
                vertices.insert(_k + 1, Pt(p.x + 1, p.y + 1))
                vertices.insert(_k + 2, Pt(p.x + 1, ny))
            break

def stalagmitable(p: Pt, bs: List[Pt]) -> Optional[int]:
    for b in bs:
        if b.x == p.x and b.y < p.y:
            return None
    return p.y

def stalactitable(p: Pt, bs: List[Pt], h: int) -> Optional[int]:
    for b in bs:
        if b.x == p.x and b.y > p.y:
            return None
    return h - p.y

def blocks(p: Pt, include: List[Pt]) -> List[Pt]:
    return []

def parseFromFile(x: str) -> Puzzle:
    y = ""
    with open(x, 'r') as fh:
        y = fh.read() 
    return Puzzle.parse(y)

def main():
    puz = parseFromFile(sys.argv[1])
    print(solve(puz))
 
if __name__ == "__main__":
    main()
