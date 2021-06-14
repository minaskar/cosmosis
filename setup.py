from setuptools import setup, find_packages
from setuptools.command.install import install
from distutils.command.build import build
from distutils.command.clean import clean
import pkg_resources
import subprocess

import os
import sys

version = open('cosmosis/version.py').read().split('=')[1].strip().strip("'")

minimum_cc_version = pkg_resources.parse_version("5.0.0")
minimum_cxx_version = pkg_resources.parse_version("5.0.0")

f90_mods = [
    "datablock/cosmosis_section_names.mod",
    "datablock/cosmosis_types.mod",
    "datablock/cosmosis_wrappers.mod",
    "datablock/cosmosis_modules.mod",
]

scripts = [
    'bin/cosmosis',
    'bin/cosmosis-configure',
    'bin/cosmosis-extract',
    'bin/cosmosis-sample-fisher',
    'bin/cosmosis-postprocess',
]

c_headers = [
    "datablock/c_datablock.h",
    "datablock/datablock_logging.h",
    "datablock/datablock_types.h",
    "datablock/cosmosis_constants.h",
    "datablock/datablock_status.h",
    "datablock/section_names.h",
]

cc_headers = [
    "datablock/clamp.hh",
    "datablock/entry.hh",
    "datablock/fakearray.hh",
    "datablock/ndarray.hh",
    "datablock/datablock.hh",
    "datablock/exceptions.hh",
    "datablock/mdarraygen.hh",
    "datablock/section.hh"
]

datablock_libs = ["datablock/libcosmosis.so"]

sampler_libs = ["samplers/multinest/multinest_src/libnest3.so",
                "samplers/multinest/multinest_src/libnest3_mpi.so",
                "samplers/polychord/polychord_src/libchord.so",
                "samplers/polychord/polychord_src/libchord_mpi.so",
                "samplers/minuit/minuit_wrapper.so"]


testing_files = [
    "test/libtest/c_datablock_complex_array_test.c",
    "test/libtest/c_datablock_double_array_test.c",
    "test/libtest/c_datablock_int_array_test.c",
    "test/libtest/c_datablock_multidim_complex_array_test.c",
    "test/libtest/c_datablock_multidim_double_array_test.c",
    "test/libtest/c_datablock_multidim_int_array_test.c",
    "test/libtest/c_datablock_test.c",
    "test/libtest/cosmosis_test.F90",
    "test/libtest/cosmosis_tests.supp",
    "test/libtest/datablock_test.cc",
    "test/libtest/entry_test.cc",
    "test/libtest/ndarray_test.cc",
    "test/libtest/section_test.cc",
    "test/libtest/test_c_datablock_scalars.h",
    "test/libtest/test_c_datablock_scalars.template",
    "test/libtest/Makefile",
]

runtime_libs = ["runtime/experimental_fault_handler.so"]

compilers_config = ["config/compilers.mk", "config/subdirs.mk"]

# if sys.platform == 'darwin':
#     from distutils import sysconfig
#     vars = sysconfig.get_config_vars()
#     vars['LDSHARED'] = vars['LDSHARED'].replace('-bundle', '-dynamiclib')

def get_COSMOSIS_SRC_DIR():
    cosmosis_src_dir = os.path.join(os.getcwd(), "cosmosis")
    return cosmosis_src_dir

def compile_library():
    cosmosis_src_dir = get_COSMOSIS_SRC_DIR()
    env = os.environ.copy()
    env["COSMOSIS_SRC_DIR"] = cosmosis_src_dir
    # User can switch on COSMOSIS_OMP manually, but it should
    # always be on for conda
    if "CONDA_PREFIX" in env:
        env["COSMOSIS_OMP"] = "1"
    env['FC'] = env.get('FC', 'gfortran')

    subprocess.check_call(["make"], env=env, cwd="cosmosis")
    

def clean_library():
    cosmosis_src_dir = get_COSMOSIS_SRC_DIR()
    env = {"COSMOSIS_SRC_DIR": cosmosis_src_dir,}
    subprocess.check_call(["make", "clean"], env=env, cwd="cosmosis")


class my_build(build):
    def run(self):
        compile_library()
        super().run()


class my_install(install):
    def __init__(self, dist):
        install.__init__(self, dist)
        self.build_args = {}
        if self.record is None:
            self.record = "install-record.txt"

    def run(self):
        super().run()

class my_clean(clean):
    def run(self):
        clean_library()
        super().run()

print("PACAKGES", find_packages())

setup(name = 'cosmosis',
        description       = "A testbed stand-alone installation of the CosmoSIS project. Not ready for primetime!",
        author            = "Joe Zuntz",
        author_email      = "joezuntz@googlemail.com",
        url               = "https://bitbucket.org/joezuntz/cosmosis",  
        packages = find_packages(),
        package_data = {"cosmosis" : datablock_libs + sampler_libs + runtime_libs 
                            + c_headers + cc_headers + f90_mods 
                            + compilers_config + testing_files,},
        scripts = scripts,
        install_requires = ['pyyaml', 'future', 'configparser', 'emcee', 'numpy', 'scipy'],
        cmdclass={"install"   : my_install,
                "build"     : my_build,
                "build_ext" : my_build,
                "clean"     : my_clean},
        version=version,
        )

