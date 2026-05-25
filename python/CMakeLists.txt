cmake_minimum_required(VERSION 3.13)

# Python bindings for VCellMovingBoundary via pybind11.
# pybind11 and Python3 are found in the parent CMakeLists.txt.

pybind11_add_module(vcellmbsolver_py
    pyvcellmbsolver.cpp
)

target_link_libraries(vcellmbsolver_py
    PRIVATE
        MovingBoundaryLib
        vcommons        # for tinyxml2
)

# The .so goes to bin/ alongside the other outputs so it is importable
# from the build tree without installation.
set_target_properties(vcellmbsolver_py PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

install(TARGETS vcellmbsolver_py
    LIBRARY DESTINATION ${Python3_SITEARCH}
)

# Install the pure-Python wrapper alongside the extension module.
install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/vcellmbsolver.py
    DESTINATION ${Python3_SITEARCH}
)

# ---------------------------------------------------------------------------
# Python tests (pytest) — run inside a dedicated virtual environment.
#
# The venv is created (or refreshed) at configure time in the build tree so
# the test environment is reproducible and isolated from the system Python.
# pytest is installed into the venv; the extension .so is made importable
# via PYTHONPATH rather than by installing it into the venv.
# ---------------------------------------------------------------------------
if(BUILD_TESTING)
    set(VENV_DIR ${CMAKE_BINARY_DIR}/python_venv)

    # Platform-specific paths inside the venv
    if(WIN32)
        set(VENV_PYTHON ${VENV_DIR}/Scripts/python.exe)
        set(VENV_PIP    ${VENV_DIR}/Scripts/pip.exe)
    else()
        set(VENV_PYTHON ${VENV_DIR}/bin/python)
        set(VENV_PIP    ${VENV_DIR}/bin/pip)
    endif()

    # Create the venv (idempotent: safe to re-run on reconfigure)
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -m venv ${VENV_DIR}
        RESULT_VARIABLE _venv_rc
    )
    if(NOT _venv_rc EQUAL 0)
        message(WARNING "Python venv creation failed (exit ${_venv_rc}). "
                        "Python tests may not run correctly.")
    endif()

    # Install pytest into the venv
    execute_process(
        COMMAND ${VENV_PIP} install --quiet pytest
        RESULT_VARIABLE _pip_rc
    )
    if(NOT _pip_rc EQUAL 0)
        message(WARNING "pip install pytest failed (exit ${_pip_rc}). "
                        "Python tests may not run correctly.")
    endif()

    add_test(
        NAME PyVcellMbSolver
        COMMAND ${VENV_PYTHON} -m pytest
                ${CMAKE_CURRENT_SOURCE_DIR}/tests
                -v --tb=short
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    )
    # PYTHONPATH makes the compiled extension and the wrapper importable
    # without installing them into the venv.
    set_tests_properties(PyVcellMbSolver PROPERTIES
        ENVIRONMENT
            "PYTHONPATH=${CMAKE_BINARY_DIR}/bin:${CMAKE_CURRENT_SOURCE_DIR}"
    )
endif()
