# Copyright 2021 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import absolute_import, print_function

import argparse
import contextlib
import hashlib
import json
import os
import pkgutil
import shutil
import stat
import sys
import zipfile

from pex.pex_bootstrapper import bootstrap_pex_env

from lambdex.version import __version__

EVENT_FUNCTION_SIGNATURE = "event"
GCP_HTTP_FUNCTION_SIGNATURE = "gcp-http"


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


class LambdexInfo(object):
    @classmethod
    def from_string(cls, blob):
        return LambdexInfo(**json.loads(blob))

    def __init__(self, entry_point):
        self.entry_point = entry_point

    def to_json(self):
        return json.dumps({"entry_point": self.entry_point})


def _write_zip_content(zf, filename, content):
    info = zipfile.ZipInfo(filename)
    info.external_attr = 0o755 << 16
    zf.writestr(info, content)


def write_lambdex_handler(pex_zip, options):
    if (options.script is not None and options.entry_point is not None) or (
        options.script is None and options.entry_point is None
    ):
        die("Must specify one of -s/--script or -e/--entry-point but not both.")

    if options.output:
        output_zip = options.output
        shutil.copy(pex_zip, output_zip)
        os.chmod(output_zip, os.stat(output_zip).st_mode | stat.S_IWRITE)
    else:
        output_zip = pex_zip

    script = None
    if options.script is not None:
        method = options.handler
        script = os.path.basename(options.script)
        filename_prefix, ext = os.path.splitext(script)
        if ext != ".py":
            die('--script must be a python file that ends with ".py"')
        # TODO(wickman) Validate that there is a symbol w/in the file that
        # matches the method using ast.parse
        entry_point = "%s:%s" % (filename_prefix, method)
    else:
        entry_point = options.entry_point

    lambdex_info = LambdexInfo(entry_point)

    with contextlib.closing(zipfile.ZipFile(output_zip, "a")) as zf:
        if script is not None:
            with open(os.path.realpath(options.script), "rb") as fp:
                _write_zip_content(zf, script, fp.read())
        _write_zip_content(zf, "LAMBDEX-INFO", lambdex_info.to_json())
        _write_zip_content(
            zf, options.module, pkgutil.get_data("lambdex.resources", "lambdex_handler.py")
        )


# lambdex build foo.pex
#   [-H handler]
#   [-M module.py]
#   [-s script.py]
#   [-e pkg:symbol]
#   [-o output_file.zip]
def build_lambdex(args):
    write_lambdex_handler(args.pex, args)


def configure_build_command(parser):
    parser = parser.add_parser(
        "build",
        help="build a lambdex package",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.set_defaults(func=build_lambdex)

    parser.add_argument(
        "pex", metavar="PEXFILE", help="The pex file to turn into a lambdex package."
    )

    parser.add_argument(
        "-s",
        "--script",
        dest="script",
        metavar="FILENAME",
        default=None,
        help="The script to include, if any.",
    )

    parser.add_argument(
        "-e",
        "--entry-point",
        dest="entry_point",
        metavar="PACKAGE:NAME",
        default=None,
        help="Set the entry point of the lambda function to this package:name tuple.",
    )

    parser.add_argument(
        "-H",
        "--script-handler",
        dest="handler",
        default="handler",
        metavar="FUNCTION",
        help="Invoke this function within the script.",
    )

    parser.add_argument(
        "-M",
        "--script-module",
        dest="module",
        default="lambdex_handler.py",
        metavar="FILENAME",
        help="Root module of the lambda.",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        default=None,
        metavar="FILENAME",
        help="Write output to this path. Otherwise, modifies the input file in-place.",
    )


def load_json_blob(filename):
    if filename == "-":
        return json.loads(sys.stdin.read())
    else:
        with open(filename, "rb") as fp:
            return json.load(fp)


CHUNK_SIZE = 64 * 1024


def hash_file(filename, hasher=hashlib.sha256):
    hash = hasher()
    with open(filename, "rb") as fp:
        for chunk in iter(lambda: fp.read(CHUNK_SIZE), b""):
            hash.update(chunk)
    return hash.hexdigest()


def unzip(filename, path):
    os.makedirs(path + "~")
    with contextlib.closing(zipfile.ZipFile(filename, "r")) as zfp:
        zfp.extractall(path=path + "~")
    os.rename(path + "~", path)


@contextlib.contextmanager
def cached_environment(root, pex_file):
    if os.path.isdir(pex_file):
        yield pex_file
        return

    sha = hash_file(pex_file)
    target = os.path.join(os.path.normpath(os.path.expanduser(root)), sha)

    if not os.path.exists(target):
        unzip(pex_file, target)

    yield target


@contextlib.contextmanager
def chdir(dirname):
    cwd = os.getcwd()
    os.chdir(dirname)
    yield
    os.chdir(cwd)


def load_entry_point(entry_point):
    if sys.version_info[:2] >= (3, 8):
        from importlib.metadata import EntryPoint

        return EntryPoint(name=None, value=entry_point, group=None).load()
    else:
        try:
            # PEX >= 1.6.0
            from pex.third_party.pkg_resources import EntryPoint
        except ImportError:
            # PEX < 1.6.0 has an install requirement of setuptools which we leverage knowledge of.
            from pkg_resources import EntryPoint
        return EntryPoint.parse("run = {ep}".format(ep=entry_point)).resolve()


# lambdex test [context configuration options] foo.pex <foo.json
def test_lambdex(args):
    bootstrap_pex_env(args.pex)

    with cached_environment(args.root, args.pex) as target:
        lambdex_entry_point = os.environ.get("LAMBDEX_ENTRY_POINT")
        if not lambdex_entry_point:
            with open(os.path.join(target, "LAMBDEX-INFO"), "rb") as fp:
                lambdex_info_blob = fp.read()

            lambdex_info = LambdexInfo.from_string(lambdex_info_blob)
            lambdex_entry_point = lambdex_info.entry_point

        sys.path.append(target)

        with chdir(target):
            runner = load_entry_point(lambdex_entry_point)
            if args.type == EVENT_FUNCTION_SIGNATURE:
                if args.empty:
                    runner({}, None)
                else:
                    for filename in args.files:
                        runner(load_json_blob(filename), None)
            elif args.type == GCP_HTTP_FUNCTION_SIGNATURE:
                import flask

                app = flask.Flask("test-app")
                if args.empty:
                    with app.test_request_context(json={}):
                        runner(flask.request)
                else:
                    for filename in args.files:
                        with app.test_request_context(json=load_json_blob(filename)):
                            runner(flask.request)


def configure_test_command(parser):
    parser = parser.add_parser(
        "test",
        help="test a lambdex package",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.set_defaults(func=test_lambdex)

    parser.add_argument(
        "pex", metavar="PEXFILE", help="The pex file to turn into a lambdex package."
    )

    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="*",
        help="A list of input json blobs to send as events to the function.",
    )

    parser.add_argument(
        "--empty",
        dest="empty",
        default=False,
        action="store_true",
        help="If specified, use an empty test event rather than reading "
        "events from the command line.",
    )

    parser.add_argument(
        "--root",
        dest="root",
        default="~/.lambdex",
        help="If specified, cache lambdex test environments here.",
    )

    parser.add_argument(
        "--type",
        dest="type",
        default=EVENT_FUNCTION_SIGNATURE,
        choices=[EVENT_FUNCTION_SIGNATURE, GCP_HTTP_FUNCTION_SIGNATURE],
        help="The type of function to be tested.",
    )


def configure_clp():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-V", "--version", action="version", version=__version__)

    def usage(_):
        parser.print_help()

    parser.set_defaults(func=usage)

    subparsers = parser.add_subparsers()
    configure_build_command(subparsers)
    configure_test_command(subparsers)
    return parser


def main(args=None):
    args = args or sys.argv[1:]

    parser = configure_clp()
    args = parser.parse_args(args=args)
    args.func(args)


if __name__ == "__main__":
    main()
