import importlib.metadata

for i in importlib.metadata.distributions():
    print(i.metadata['Name'])

import cmlibs.maths
import cmlibs.utils


def add(a, b):
    return a + b

