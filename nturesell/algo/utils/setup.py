from distutils.core import setup, Extension

cutil_module = Extension('cutil', sources=['cutil.c'])
setup(name='CUtil',
    description='A package containing modules for implement some utility functions in C',
    ext_modules=[cutil_module],
)