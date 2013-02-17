from __future__ import print_function
from __future__ import absolute_import

__all__ = ['PyPath']

import ctypes
import sys
import pkg_resources


class PyPath:

    @staticmethod
    def builtin_path():
        """Consumes the C API Py_GetPath function to return the path
        built into the Python interpreter.
        This already takes care of PYTHONPATH.

        Note: actually Py_GetPath dynamically computes the path on
        the first call (which happens during startup).
        """

        Py_GetPath = ctypes.pythonapi.Py_GetPath
        if sys.version_info[0] >= 3:
            # Unicode
            Py_GetPath.restype = ctypes.c_wchar_p
        else:
            Py_GetPath.restype = ctypes.c_char_p

        return Py_GetPath().split(':')

    @staticmethod
    def path_for_pkg_name(pkg_name):
        pkgs = [pkg for pkg in pkg_resources.working_set
                if pkg.project_name == pkg_name]
        if len(pkgs) == 0:
            return None
        return pkgs[0].location

    @classmethod
    def bundler_path(cls):
        """Returns the path to PBundler itself."""

        return cls.path_for_pkg_name("pbundler")

    @classmethod
    def clean_path(cls):
        """Return a list containing the builtin_path and bundler_path.
        Before replacing sys.path with this, realize that sys.path[0]
        will be missing from this list.
        """

        path = [cls.bundler_path()] + cls.builtin_path()
        return path

    @classmethod
    def replace_sys_path(cls, new_path):
        for path in sys.path:
            sys.path.remove(path)
        sys.path.extend(new_path)


PyPath.initial_sys_path_0 = sys.path[0]
