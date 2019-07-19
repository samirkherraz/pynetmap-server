import os
from distutils.core import Extension, setup

from Cython.Build import cythonize

xfiles = ['__main__.py', '__init__.py', 'proxy.py', '__pycache__', 'setup.py']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRENTDIR = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if CURRENTDIR != "build":
    print(f' Current dir : {CURRENTDIR} is not the build dir')
    exit(0)
SUBDIRS = [x for x in os.listdir(
    BASE_DIR) if os.path.isdir(x) and x not in xfiles]
for d in SUBDIRS:
    print(f'{d}')
    Modules = [x for x in os.listdir(os.path.abspath(d)) if x not in xfiles]
    for module_dir in Modules:
        if "." not in module_dir and module_dir not in xfiles:
            for module in [x for x in os.listdir(os.path.abspath(d)+"/"+module_dir) if x not in xfiles and x.endswith('.py')]:
                print(module)

                mname = module.replace('.py', '')
                ext = Extension(name=f'{d}.{module_dir}.{mname}', sources=[
                                f'{d}/{module_dir}/{module}'])
                setup(ext_modules=cythonize(ext))
                os.system(
                    f'rm {d}/{module_dir}/{mname}.* ; mv ./build/lib*/{d}/{module_dir}/{mname}* {d}/{module_dir}/{mname}.so ')


SUBFILES = [x for x in os.listdir(
    BASE_DIR) if x.endswith('.py') and x not in xfiles]

for f in SUBFILES:
    mname = f.replace('.py', '')
    ext = Extension(name=f'{mname}',
                    sources=[f'{f}'])
    setup(ext_modules=cythonize(ext))
    cmd = f'rm ./{mname}.* ; mv ./build/lib*/{mname}* ./{mname}.so '
    print(cmd)
    os.system(cmd)
