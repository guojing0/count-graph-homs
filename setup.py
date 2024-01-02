from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize(["local_hom_count_pyx.pyx", "helper_functions.pyx"])
)
