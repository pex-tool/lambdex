# takes requirements or requirements.txt, should accept no other options:
#    --python needs to be python2.7
#    --platform needs to be linux-x86_64
#
#

from __future__ import absolute_import

import contextlib
import os
import sys
import zipfile
from optparse import OptionParser

from pex.common import die, safe_mkdtemp, safe_delete
from pex.pex_builder import PEXBuilder
from pex.interpreter import PythonInterpreter
from pex.resolver_options import ResolverOptionsBuilder
from pex.resolvable import Resolvable
from pex.resolver import CachingResolver, Resolver
from pex.requirements import requirements_from_file

from pex.bin.pex import (
    configure_clp_pex_resolution,
    configure_clp_pex_environment,
    interpreter_from_options)
    

STATIC_OPTIONS = {
  'python': 'python2.7',
  'platform': 'linux-x86_64',
  'pex_root': '~/.pex',
}


LAMBDEX_TEMPLATE = b"""
import os
import sys

__entry_point__ = None
if '__file__' in locals() and __file__ is not None:
  __entry_point__ = os.path.dirname(__file__)
elif '__loader__' in locals():
  from zipimport import zipimporter
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
                                                                
from _pex.pex_bootstrapper import bootstrap_pex_env
bootstrap_pex_env(__entry_point__)

from pkg_resources import EntryPoint
__RUNNER = EntryPoint.parse('run = {0}').resolve()

def handler(*args, **kw):
  return __RUNNER(*args, **kw)                    
"""


   

def configure_clp():
  usage = (  
    '%prog [-o HANDLER.ZIP] [-e ENTRY_POINT] req1 req2 ...\n\n'
    '%prog builds an AWS Lambda deployment package based on the given specifications: '
    'sources, requirements, their dependencies and other options.')
                    
  parser = OptionParser(usage=usage, version='%prog 0.1.0')

  resolver_options_builder = ResolverOptionsBuilder()
  configure_clp_pex_resolution(parser, resolver_options_builder)
  configure_clp_pex_environment(parser)
  
  parser.add_option(
      '-o', '--output-file',
      dest='pex_name',
      default='handler.zip',
      help='The name of the output lambda zipfile.')

  parser.add_option(
      '-e', '--entry-point',
      dest='entry_point',
      metavar='SYMBOL:NAME',
      default=None,
      help='Set the entry point of the lambda function to this symbol:name tuple.')
  
  parser.add_option(
      '--filename',
      dest='filename',
      default=None,
      help='Package this file within the handler.')
  
  parser.add_option(
      '--handler',
      dest='handler',
      default=None,
      help='Set the handler within the lambda zipfile, used in conjunction with --filename.')
  
  parser.add_option(
      '-r', '--requirement',
      dest='requirement_files',
      metavar='FILE',
      default=[],
      type=str,
      action='append',
      help='Add requirements from the given requirements file.  This option can be used multiple '
           'times.')

  return parser, resolver_options_builder


def write_lambdex_handler(pex_zip, options):
  entry_point = options.entry_point
  filename = options.filename
  handler = options.handler
  
  if entry_point is None and handler is None:
    die('Must specify one of --handler or --entry-point.')
  
  if (handler is not None and filename is None) or (handler is None and filename is not None):
    die('--filename and --handler must both be specified.')
  
  # ugh validate idk
  if handler:
    filename_prefix, ext = os.path.splitext(os.path.filename(filename))
    if ext != '.py': 
      die('filename must be a python file that ends with ".py"')
    if len(handler.split('.')) != 2:
      die('handler must be of the form package.method')
    package, method = handler.split('.')
    if package != filename_prefix:
      die('handler package is not the same as the filename.')
    entry_point = '%s:%s' % (package, method)

  with contextlib.closing(zipfile.ZipFile(pex_zip, 'a')) as zf:
    if handler:
      zf.write(filename, arcname=os.path.filename(filename))
    zf.writestr('lambdex.py', LAMBDEX_TEMPLATE.format(entry_point))


def make_pex(args, options, resolver_option_builder):
  interpreter = interpreter_from_options(options)
  
  # validate interpreter
  
  pex_builder = PEXBuilder(path=safe_mkdtemp(), interpreter=interpreter)
  resolvables = [Resolvable.get(arg, resolver_option_builder) for arg in args]
  
  for requirements_txt in options.requirement_files:
    resolvables.extend(requirements_from_file(requirements_txt, resolver_options_builder))
  
  resolver_kwargs = dict(interpreter=interpreter, platform=STATIC_OPTIONS['platform'])
  if options.cache_dir:
    resolver = CachingResolver(options.cache_dir, options.cache_ttl, **resolver_kwargs)
  else:
    resolver = Resolver(**resolver_kwargs)

  resolveds = resolver.resolve(resolvables)
  
  for dist in resolveds:
    pex_builder.add_distribution(dist)
    pex_builder.add_requirement(dist.as_requirement())
  
  return pex_builder


def main(args=None):
  args = args or sys.argv[1:]
  
  parser, resolver_options_builder = configure_clp()
  parser.set_default('python', STATIC_OPTIONS['python'])
  parser.set_default('platform', STATIC_OPTIONS['platform'])
  
  options, reqs = parser.parse_args(args=args)
  
  # This is terrible -- the pex --pex-root option is not composable via the configure_clp options.
  # This should be fixed upstream.  Similarly, ENV is a global -- we should not be polluting global
  # options like this.  This is a conflation of runtime and build time state.
              
  # Don't alter cache if it is disabled.
  pex_root = os.path.expanduser(STATIC_OPTIONS['pex_root'])
  if options.cache_dir:
    options.cache_dir = os.path.normpath(options.cache_dir.format(pex_root=pex_root))
  options.interpreter_cache_dir = os.path.normpath(options.interpreter_cache_dir.format(pex_root=pex_root))
  
  pex_builder = make_pex(reqs, options, resolver_options_builder)
  
  tmp_name = options.pex_name + '~'
  safe_delete(tmp_name)
  pex_builder.build(tmp_name)

  if options.entry_point is None:
    die('Must specify --entry-point.')
    
  write_lambdex_handler(tmp_name, options)

  os.rename(tmp_name, options.pex_name)


if __name__ == '__main__':
  main()
