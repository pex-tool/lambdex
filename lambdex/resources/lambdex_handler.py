import os
import sys

__entry_point__ = None
if '__file__' in locals() and __file__ is not None:
  __entry_point__ = os.path.dirname(__file__)
elif '__loader__' in locals():
  from pkgutil import ImpLoader
  if hasattr(__loader__, 'archive'):
    __entry_point__ = __loader__.archive
  elif isinstance(__loader__, ImpLoader):
    __entry_point__ = os.path.dirname(__loader__.get_filename())

if __entry_point__ is None:
  sys.stderr.write('Could not launch python executable!\\n')
  sys.exit(2)

sys.path[0] = os.path.abspath(sys.path[0])
sys.path.insert(0, os.path.abspath(os.path.join(__entry_point__, '.bootstrap')))

try:
  # PEX >= 1.6.0
  from pex.third_party.pkg_resources import EntryPoint as __EntryPoint
  from pex.pex_bootstrapper import bootstrap_pex_env, is_compressed
except ImportError:
  # PEX < 1.6.0 has an install requirement of setuptools which we leverage knowledge of.
  from pkg_resources import EntryPoint as __EntryPoint
  from _pex.pex_bootstrapper import bootstrap_pex_env, is_compressed

bootstrap_pex_env(__entry_point__)

if is_compressed(__entry_point__):
  import contextlib, zipfile
  with contextlib.closing(zipfile.ZipFile(__entry_point__)) as zf:
    __lambdex_info_blob = zf.read('LAMBDEX-INFO')
else:
  with open(os.path.join(__entry_point__, 'LAMBDEX-INFO'), 'rb') as fp:
    __lambdex_info_blob = fp.read()

import json as __json
__lambdex_info = __json.loads(__lambdex_info_blob)
__RUNNER = __EntryPoint.parse('run = %s' % __lambdex_info['entry_point']).resolve()

def handler(event, context):
  return __RUNNER(event, context)
