# See production/build_cpp_ext/README.md
from production.build_cpp_ext import magic_extension
magic_extension(
    name='cpp_grid_ext',
    sources=['cpp_grid.cpp'],
    headers=['basics.h'])

from production.cpp_grid.cpp_grid_ext import Pt, CharGrid, ByteGrid, IntGrid
