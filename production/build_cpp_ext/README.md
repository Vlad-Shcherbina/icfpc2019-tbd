The idea is that you edit C++ code, then run Python script that uses it,
and it recompiles it if necessary behind the scenes.

Example usage is in `production/examples/cpp_demo/__init__.py`.

To see it in action run the following command:
```
python -m production.examples.cpp_demo.demo
```

There are two environment variables to control compilation process:
- `TBD_RELEASE`
  - `"0"` (default) - debug build, expensive defensive checks
  - `"1"` - release build, optimized
- `TBD_BUILD_METHOD`
  - `"manual"` (default) - directly invoke compilers with carefully chosen flags
  - `"distutils"` - use distutils' extension-building machinery


### Differences between "manual" and "distutils"

"Distutils" looks at timestamps to determine whether recompilation is necessary.
If you touch any file, everything will be rebuilt from scratch.
"Manual" looks at file content. It does not recompile translation units that were not affected by a change.

"Manual" compiles different translation units in parallel.

Unlike "distutils", "manual" requires "cl.exe" or "g++" to be in PATH.

"Distutils" supposedly handles all possible corner cases and weird configurations.
"Manual" works on my machine.
