# Copyright 2021 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

# N.B.: Flit uses this as our distribution description.
"""Lambdex turns pex files into aws lambda python functions."""

from __future__ import absolute_import

from .version import __version__ as __lambdex_version__

__version__ = __lambdex_version__  # N.B.: Flit uses this as out distribution version.
