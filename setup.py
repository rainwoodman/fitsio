import distutils
from distutils.core import setup, Extension, Command
import os
import sys
import numpy
import glob
import shutil
import platform

libs = []

if "--use-system-fitsio" not in sys.argv:
    compile_fitsio_package = True
else:
    compile_fitsio_package = False
    sys.argv.remove("--use-system-fitsio")

extra_objects = None
include_dirs=[numpy.get_include()]
if platform.system()=='Darwin':
    extra_compile_args=['-arch','x86_64']
    extra_link_args=['-arch','x86_64']
else:
    extra_compile_args=[]
    extra_link_args=[]
    
if compile_fitsio_package:
    package_basedir = os.path.abspath(os.curdir)

    #cfitsio_version = '3280patch'
    cfitsio_version = '3370patch'
    cfitsio_dir = 'cfitsio%s' % cfitsio_version
    cfitsio_build_dir = os.path.join('build',cfitsio_dir)
    cfitsio_zlib_dir = os.path.join(cfitsio_build_dir,'zlib')
    
    makefile = os.path.join(cfitsio_build_dir, 'Makefile')

    def copy_update(dir1,dir2):
        f1 = os.listdir(dir1)
        for f in f1:
            path1 = os.path.join(dir1,f)
            path2 = os.path.join(dir2,f)

            if os.path.isdir(path1):
                if not os.path.exists(path2):
                    os.makedirs(path2)
                copy_update(path1,path2)
            else:
                if not os.path.exists(path2):
                    shutil.copy(path1,path2)
                else:
                    stat1 = os.stat(path1)
                    stat2 = os.stat(path2)
                    if (stat1.st_mtime > stat2.st_mtime):
                        shutil.copy(path1,path2)

    def configure_cfitsio():
        os.chdir(cfitsio_build_dir)
        ret=os.system('sh ./configure --with-bzip2')
        if ret != 0:
            raise ValueError("could not configure cfitsio %s" % cfitsio_version)
        os.chdir(package_basedir)

    def compile_cfitsio():
        os.chdir(cfitsio_build_dir)
        ret=os.system('make')
        if ret != 0:
            raise ValueError("could not compile cfitsio %s" % cfitsio_version)
        os.chdir(package_basedir)


    if not os.path.exists('build'):
        ret=os.makedirs('build')

    if not os.path.exists(cfitsio_build_dir):
        ret=os.makedirs(cfitsio_build_dir)

    copy_update(cfitsio_dir, cfitsio_build_dir)

    if not os.path.exists(makefile):
        configure_cfitsio()

    compile_cfitsio()

    # when using "extra_objects" in Extension, changes in the objects do *not*
    # cause a re-link!  The only way I know is to force a recompile by removing the
    # directory
    build_libdir=glob.glob(os.path.join('build','lib*'))
    if len(build_libdir) > 0:
        shutil.rmtree(build_libdir[0])

    extra_objects = glob.glob(os.path.join(cfitsio_build_dir,'*.o'))
    extra_objects += glob.glob(os.path.join(cfitsio_zlib_dir,'*.o'))

    include_dirs.append(cfitsio_dir)

if not compile_fitsio_package:
    extra_link_args.append('-lcfitsio')

sources = ["fitsio/fitsio_pywrap.c"]
data_files=[]

if compile_fitsio_package:
    # If configure detected bzlib.h, we have to link to libbz2.so
    if '-DHAVE_BZIP2=1' in open(os.path.join(cfitsio_build_dir, 'Makefile')).read():
        libs.append('bz2')
else:
    # Include bz2 by default?  Depends on how system cfitsio was built.
    pass

ext=Extension("fitsio._fitsio_wrap", 
              sources,
              libraries=libs,
              extra_objects=extra_objects,
              extra_compile_args=extra_compile_args, 
              extra_link_args=extra_link_args,
              include_dirs=include_dirs)

description = ("A full featured python library to read from and "
               "write to FITS files.")

long_description=open(os.path.join(os.path.dirname(__file__), "README.md")).read()

classifiers = ["Development Status :: 5 - Production/Stable"
               ,"License :: OSI Approved :: GNU General Public License (GPL)"
               ,"Topic :: Scientific/Engineering :: Astronomy"
               ,"Intended Audience :: Science/Research"
              ]

try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

setup(name="fitsio", 
      version="0.9.8rc1",
      description=description,
      long_description=long_description,
      license = "GPL",
      classifiers=classifiers,
      url="https://github.com/esheldon/fitsio",
      author="Erin Scott Sheldon",
      author_email="erin.sheldon@gmail.com",
      install_requires=['numpy'],
      packages=['fitsio'],
      data_files=data_files,
      ext_modules=[ext],
      cmdclass = {"build_py":build_py})



