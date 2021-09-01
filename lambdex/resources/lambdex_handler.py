# Copyright 2021 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

import os
import sys

__entry_point__ = None
if "__file__" in locals() and __file__ is not None:
    __entry_point__ = os.path.dirname(__file__)
elif "__loader__" in locals():
    from pkgutil import ImpLoader

    if hasattr(__loader__, "archive"):
        __entry_point__ = __loader__.archive
    elif isinstance(__loader__, ImpLoader):
        __entry_point__ = os.path.dirname(__loader__.get_filename())

if __entry_point__ is None:
    sys.stderr.write("Could not launch python executable!\\n")
    sys.exit(2)

sys.path[0] = os.path.abspath(sys.path[0])
sys.path.insert(0, os.path.abspath(os.path.join(__entry_point__, ".bootstrap")))

try:
    # PEX >= 1.6.0
    from pex.pex_bootstrapper import bootstrap_pex_env
    from pex.third_party.pkg_resources import EntryPoint as __EntryPoint
except ImportError:
    # PEX < 1.6.0 has an install requirement of setuptools which we leverage knowledge of.
    from _pex.pex_bootstrapper import bootstrap_pex_env
    from pkg_resources import EntryPoint as __EntryPoint

bootstrap_pex_env(__entry_point__)

__lambdex_entry_point = os.environ.get("LAMBDEX_ENTRY_POINT")

if not __lambdex_entry_point:
    import json as __json
    import zipfile

    if zipfile.is_zipfile(__entry_point__):
        import contextlib

        with contextlib.closing(zipfile.ZipFile(__entry_point__)) as zf:
            __lambdex_info_blob = zf.read("LAMBDEX-INFO")
    else:
        with open(os.path.join(__entry_point__, "LAMBDEX-INFO"), "rb") as fp:
            __lambdex_info_blob = fp.read()

    __lambdex_info = __json.loads(__lambdex_info_blob)
    __lambdex_entry_point = __lambdex_info["entry_point"]

__RUNNER = __EntryPoint.parse("run = %s" % __lambdex_entry_point).resolve()


def handler(*args, **kwargs):
    return __RUNNER(*args, **kwargs)
