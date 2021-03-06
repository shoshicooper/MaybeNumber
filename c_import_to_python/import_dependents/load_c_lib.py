"""
(c) 2022 Shoshi (Sharon) Cooper.  No duplication is permitted for commercial use.  Any significant changes made must be
stated explicitly and the original source code, if used, must be available and credited to Shoshi (Sharon) Cooper.
"""

import os
import ctypes as ct


def load_library(path_to_library, file_name):
    os.add_dll_directory(path_to_library)
    joiner = "" if path_to_library.endswith('/') else '/'
    path = os.path.dirname(os.path.realpath(__file__))
    libc = ct.CDLL(os.path.join(path, f"{path_to_library}{joiner}{file_name}"), winmode=0)
    return libc
