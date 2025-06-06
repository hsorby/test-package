import importlib.metadata

for i in importlib.metadata.distributions():
    print(i.metadata['Name'], i._normalized_name)

import cmlibs.maths
import cmlibs.utils


def add(a, b):
    return a + b

