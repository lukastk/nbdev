"""Exporting a notebook to a library"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/04_export.ipynb.

# %% auto 0
__all__ = ['ExportModuleProc', 'black_format', 'scrub_magics', 'optional_procs', 'nb_export']

# %% ../nbs/api/04_export.ipynb
from .config import *
from .maker import *
from .imports import *
from .process import *

from fastcore.script import *
from fastcore.basics import *
from fastcore.imports import *
from fastcore.meta import *

from collections import defaultdict

# %% ../nbs/api/04_export.ipynb
class ExportModuleProc:
    "A processor which exports code to a module"
    def begin(self): self.modules,self.in_all = defaultdict(L),defaultdict(L)
    def _default_exp_(self, cell, exp_to): self.default_exp = exp_to
    def _exporti_(self, cell, exp_to=None): self.modules[ifnone(exp_to, '#')].append(cell)
    def _export_(self, cell, exp_to=None):
        self._exporti_(cell, exp_to)
        self.in_all[ifnone(exp_to, '#')].append(cell)
    def __call__(self, cell):
        src = cell.source
        if not src: return
        if cell.cell_type=='markdown' and src.startswith('# '): self.modules['#'].append(cell)
    _exports_=_export_

# %% ../nbs/api/04_export.ipynb
def black_format(cell, # Cell to format
                 force=False): # Turn black formatting on regardless of settings.ini
    "Processor to format code with `black`"
    try: cfg = get_config()
    except FileNotFoundError: return
    if (not cfg.black_formatting and not force) or cell.cell_type != 'code': return
    try: import black
    except: raise ImportError("You must install black: `pip install black` if you wish to use black formatting with nbdev")
    else:
        _format_str = partial(black.format_str, mode = black.Mode())
        try: cell.source = _format_str(cell.source).strip()
        except: pass

# %% ../nbs/api/04_export.ipynb
# includes the newline, because calling .strip() would affect all cells.
_magics_pattern = re.compile(r'^\s*(%%|%).*\n?', re.MULTILINE)

def scrub_magics(cell): # Cell to format
    "Processor to remove cell magics from exported code"
    try: cfg = get_config()
    except FileNotFoundError: return
    if cell.cell_type != 'code': return
    try: cell.source = _magics_pattern.sub('', cell.source)
    except: pass

# %% ../nbs/api/04_export.ipynb
import nbdev.export
def optional_procs():
    "An explicit list of processors that could be used by `nb_export`"
    return L([p for p in nbdev.export.__all__
              if p not in ["nb_export", "nb_export_cli", "ExportModuleProc", "optional_procs"]])

# %% ../nbs/api/04_export.ipynb
def nb_export(nbname:str,        # Filename of notebook 
              lib_path:str=None, # Path to destination library.  If not in a nbdev project, defaults to current directory.
              procs=None,        # Processors to use
              name:str=None,     # Name of python script {name}.py to create.
              mod_maker=ModuleMaker,
              debug:bool=False,  # Debug mode
              fmt:str=None,      # Format to export to
             ):
    "Create module(s) from notebook"
    if lib_path is None: lib_path = get_config().lib_path if is_nbdev() else '.'
    exp = ExportModuleProc()
    nb = NBProcessor(nbname, [exp]+L(procs), debug=debug, fmt=fmt)
    nb.process()
    for mod,cells in exp.modules.items():
        if first(1 for o in cells if o.cell_type=='code'):
            all_cells = exp.in_all[mod]
            nm = ifnone(name, getattr(exp, 'default_exp', None) if mod=='#' else mod)
            if not nm:
                warn(f"Notebook '{nbname}' uses `#|export` without `#|default_exp` cell.\n"
                     "Note nbdev2 no longer supports nbdev1 syntax. Run `nbdev_migrate` to upgrade.\n"
                     "See https://nbdev.fast.ai/getting_started.html for more information.")
                return
            mm = mod_maker(dest=lib_path, name=nm, nb_path=nbname, is_new=bool(name) or mod=='#')
            mm.make(cells, all_cells, lib_path=lib_path)
