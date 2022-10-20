#!/usr/bin/env python

from __future__ import print_function

import os
import subprocess
import sys
from argparse import ArgumentParser


def main(dest):
    # N.B.: Pex outputs --version to STDERR under Python 2.7 argparse; so we capture both streams.
    output = subprocess.check_output(args=["pex", "--version"], stderr=subprocess.STDOUT)

    # iN.B.: Older versions of Pex respond to --version with 'pex <version>' whereas newer versions
    # of Pex just respond with '<version>'.
    pex_version = output.decode("utf-8").strip().split(" ", 1)[-1]

    pex_requirement = "pex=={version}".format(version=pex_version)
    print(
        "Using {pex_requirement} to build a Lambdex PEX.".format(pex_requirement=pex_requirement),
        file=sys.stderr,
    )
    subprocess.check_call(
        args=["pex", "--python", sys.executable, ".", pex_requirement, "-c", "lambdex", "-o", dest]
    )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("dest", nargs=1)
    options = parser.parse_args()
    main(options.dest[0])
