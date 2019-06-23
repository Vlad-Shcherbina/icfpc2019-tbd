import sys

from production.data_formats import Puzzle, Task, Booster
from production.geom import Pt, rasterize_poly
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
    omit.sort(key=lambda p: p.x)
    tentacles = []
    for p in omit:
        mit = stalagmitable(p, include)
        if mit is not None:
            mkStalagmite(vertices, p)
            continue
        tentacles.append(p)
    for p in tentacles:
        if mkTentacle(vertices, include, p) is None:
            assert False, (
                "Point", str(p),
                "is blocked. Closest we can get is",
                min(vertices, key=p.manhattan_dist)
            )
    return Task(border=vertices, start=Pt(0,149), obstacles=[], boosters=[])

def mkTentacle(wall, include, p):

    def new_frontierX(s, p):
        if p.y > s.y:
            tb = 1
        if p.y == s.y:
            tb = 0
        if p.y < s.y:
            tb = -1
        if p.x > s.x:
            rl = 1
        if p.x == s.x:
            rl = 0
        if p.x < s.x:
            rl = -1
        if tb != 0:
            return (Pt(s.x, s.y + tb))
        if rl != 0:
            return (Pt(s.x + rl, s.y))
        return p

    def new_frontierY(s, p):
        if p.y > s.y:
            tb = 1
        if p.y == s.y:
            tb = 0
        if p.y < s.y:
            tb = -1
        if p.x > s.x:
            rl = 1
        if p.x == s.x:
            rl = 0
        if p.x < s.x:
            rl = -1
        if tb != 0:
            return (Pt(s.x, s.y + tb))
        if rl != 0:
            return (Pt(s.x + rl, s.y))
        return p

    s = min(wall, key=p.manhattan_dist)

    (_s, p) = new_frontierY(s, p)
    _ok_square = s
    _path = []
    while _s != p: # Work till we get there
        while pt_in_poly(_s, wall): # Slide through the wall squares
            _ok_square = _s         # to get to interesting stuff
            (_s, p) = new_frontierY(_s, p)
        if _s in include:
            # switch direction
        if existsExternalWallTouching(_s, wall):
            # switch direction
        _path.append(_s)
        _ok_square = _s     
        (_s, p) = new_frontierY(_s, p)
    return None

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
