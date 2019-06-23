# See production/build_cpp_ext/README.md
from production.build_cpp_ext import magic_extension
magic_extension(
    name='cpp_game',
    sources=['cpp_game.cpp'],
    headers=[])
