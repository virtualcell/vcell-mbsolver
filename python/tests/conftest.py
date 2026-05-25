"""pytest configuration for vcellmbsolver tests.

The C++ Universe<2> singleton must be destroyed between test functions so
that each test that calls from_xml() (or setup_from_xml()) starts with a
fresh, uninitialized universe.
"""

import pytest
import vcellmbsolver_py as _mb


@pytest.fixture(autouse=True)
def reset_universe():
    """Tear down the Universe<2> singleton after every test."""
    yield
    _mb.universe_destroy()
