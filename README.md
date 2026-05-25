# VCell Moving Boundary Solver

A C++ solver library for moving-boundary problems in biological systems.
A single build produces three artifacts:

| Artifact | Description |
|---|---|
| `MovingBoundarySolver` | Standalone command-line binary |
| `libMovingBoundaryLib` | Linkable static (or shared) library |
| `vcellmbsolver_py` | Python extension module (pybind11) |

---

## Prerequisites

### All platforms

| Dependency | Notes |
|---|---|
| CMake ≥ 3.13 | <https://cmake.org/download/> |
| C++14 compiler | GCC 7+, Clang 6+, MSVC 2017+ |
| HDF5 (C + C++) | See platform sections below |
| Python 3 + headers | Python 3.8+ recommended |
| pybind11 | `pip install pybind11` or system package |
All former VCell monorepo dependencies (**FronTier**, **ExpressionParser**,
**vcommons**) are bundled in this repo and built automatically — no external
paths required.

---

## Building

### Ubuntu / Debian

```bash
# System dependencies
sudo apt-get install cmake libhdf5-dev python3-dev python3-pip
pip3 install pybind11

# Configure (substitute your actual library paths)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

# Build everything
cmake --build build --parallel
```

Output files land in `build/bin/`:

```
build/bin/
  MovingBoundarySolver        # binary
  libMovingBoundaryLib.a      # static library
  vcellmbsolver_py.cpython-*.so  # Python module
```

---

### macOS

```bash
# Dependencies via Homebrew
brew install cmake hdf5 python pybind11

# Configure
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

# Build everything
cmake --build build --parallel
```

For Apple Silicon the build system detects the architecture automatically and
sets `-DCMAKE_OSX_ARCHITECTURES=arm64`. On Intel Macs it sets `x86_64`.

---

### Windows (Visual Studio)

Install prerequisites:
- [CMake](https://cmake.org/download/)
- [Python 3](https://www.python.org/downloads/) (check "Add to PATH")
- HDF5: use the official HDF Group Windows installer or [vcpkg](https://vcpkg.io)
  (`vcpkg install hdf5`)
- pybind11: `pip install pybind11` or vcpkg (`vcpkg install pybind11`)

```bat
cmake -S . -B build

cmake --build build --config Release --parallel
```

If using vcpkg, add `-DCMAKE_TOOLCHAIN_FILE=C:\vcpkg\scripts\buildsystems\vcpkg.cmake`
to the configure step so CMake finds the vcpkg-installed packages automatically.

Output files land in `build\bin\Release\`.

---

## Build options

| CMake variable | Default | Description |
|---|---|---|
| `CMAKE_BUILD_TYPE` | `Release` | `Release`, `Debug`, `RelWithDebInfo`, `MinSizeRel` |
| `BUILD_SHARED_LIBS` | `OFF` | Build `libMovingBoundaryLib` as a shared library instead of static |
| `BUILD_TESTING` | `ON` | Also build the `TestMovingBoundary` test executable |
| `VARIABLE_SPECIES_STORAGE` | `OFF` | Enable dynamic species storage (`-DMB_VARY_MASS`) |

Example — debug build, shared library, no tests:

```bash
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Debug \
  -DBUILD_SHARED_LIBS=ON \
  -DBUILD_TESTING=OFF \
cmake --build build --parallel
```

---

## Running the tests

Tests are built by default (`BUILD_TESTING=ON`). After a successful build:

```bash
cd build
ctest --output-on-failure
```

### Test suites

All three suites run automatically when you invoke `ctest`. The Python tests
require `pytest` (`pip install pytest`).

| Suite | Name in ctest | Framework |
|---|---|---|
| Moving boundary unit tests (~150 cases) | `TestMovingBoundary.*` | Google Test |
| Expression parser smoke test | `ExpressionParserTest` | custom main |
| Python wrapper tests | `PyVcellMbSolver` | pytest |

### Python test prerequisites

No manual setup required. CMake creates an isolated virtual environment in
`build/python_venv/` at configure time and installs `pytest` into it
automatically. The venv is recreated on every `cmake -S . -B build` run.

The Python tests import `vcellmbsolver_py` (the compiled extension) and
`vcellmbsolver` (the pure-Python wrapper in `python/`). ctest sets
`PYTHONPATH` so both are importable from the build tree without installation.

### Useful ctest options

```bash
# Run in parallel
ctest --output-on-failure -j$(nproc)

# Run only tests whose name matches a pattern
ctest --output-on-failure -R "algo"
ctest --output-on-failure -R "ExpressionParser"
ctest --output-on-failure -R "PyVcellMbSolver"

# List all registered tests without running them
ctest -N

# Show full output even for passing tests
ctest -V
```

### Running the Python tests directly

After configuring, the venv already has `pytest` installed. Run the suite
directly using the venv's Python:

```bash
PYTHONPATH=build/bin:python build/python_venv/bin/python -m pytest python/tests -v
```

On Windows, substitute `build\python_venv\Scripts\python.exe`.

### Skipping tests

Pass `-DBUILD_TESTING=OFF` at configure time to skip building and registering
the test executables entirely (this also disables the Python tests):

```bash
cmake -S . -B build -DBUILD_TESTING=OFF
```

---

## Using the binary

```bash
./build/bin/MovingBoundarySolver <input.xml> <output.h5>
```

The input file format is described in `metadata/MovingBoundarySolverInputFile.docx`
and validated by `Solver/MovingBoundarySetup.xsd`.

---

## Linking the library

Add to your project's `CMakeLists.txt`:

```cmake
find_library(MB_LIB MovingBoundaryLib HINTS /path/to/vcell-mbsolver/build/bin)
find_path(MB_INCLUDE MovingBoundaryParabolicProblem.h
    HINTS /path/to/vcell-mbsolver/Solver/include)

target_link_libraries(my_target PRIVATE ${MB_LIB})
target_include_directories(my_target PRIVATE ${MB_INCLUDE})
```

Or install the project first and use the installed headers under
`<prefix>/include/vcell-mbsolver/`.

---

## Using the Python module

```python
import sys
sys.path.insert(0, "/path/to/vcell-mbsolver/build/bin")

import vcellmbsolver_py
# See python/pyvcellmbsolver.cpp for the exposed API
```

After `cmake --install build --prefix /usr/local`, the module is installed to the
active Python's `site-packages` and importable directly:

```python
import vcellmbsolver_py
```
