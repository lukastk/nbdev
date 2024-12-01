"""A YAML and formatted-markdown frontmatter processor"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/09_frontmatter.ipynb.

# %% auto 0
__all__ = ['FrontmatterProc']

# %% ../nbs/api/09_frontmatter.ipynb
from .imports import *
from .process import *
from .doclinks import _nbpath2html

from execnb.nbio import *
from fastcore.imports import *
import yaml

# %% ../nbs/api/09_frontmatter.ipynb
_RE_FM_BASE=r'''^---\s*
(.*?\S+.*?)
---\s*'''

_re_fm_nb = re.compile(_RE_FM_BASE+'$', flags=re.DOTALL)
_re_fm_md = re.compile(_RE_FM_BASE, flags=re.DOTALL)

def _fm2dict(s:str, nb=True):
    "Load YAML frontmatter into a `dict`"
    re_fm = _re_fm_nb if nb else _re_fm_md
    match = re_fm.search(s.strip())
    return yaml.safe_load(match.group(1)) if match else {}

def _md2dict(s:str):
    "Convert H1 formatted markdown cell to frontmatter dict"
    if '#' not in s: return {}
    m = re.search(r'^#\s+(\S.*?)\s*$', s, flags=re.MULTILINE)
    if not m: return {}
    res = {'title': m.group(1)}
    m = re.search(r'^>\s+(\S.*?)\s*$', s, flags=re.MULTILINE)
    if m: res['description'] = m.group(1)
    r = re.findall(r'^-\s+(\S.*:.*\S)\s*$', s, flags=re.MULTILINE)
    if r:
        try: res.update(yaml.safe_load('\n'.join(r)))
        except Exception as e: warn(f'Failed to create YAML dict for:\n{r}\n\n{e}\n')
    return res

# %% ../nbs/api/09_frontmatter.ipynb
def _dict2fm(d): return f'---\n{yaml.dump(d)}\n---\n\n'
def _insertfm(nb, fm): nb.cells.insert(0, mk_cell(_dict2fm(fm), 'raw'))

class FrontmatterProc(Processor):
    "A YAML and formatted-markdown frontmatter processor"
    def begin(self): self.fm = getattr(self.nb, 'frontmatter_', {})

    def _update(self, f, cell):
        s = cell.get('source')
        if not s: return
        d = f(s)
        if not d: return
        self.fm.update(d)
        cell.source = None

    def cell(self, cell):
        if cell.cell_type=='raw': self._update(_fm2dict, cell)
        elif cell.cell_type=='markdown' and 'title' not in self.fm: self._update(_md2dict, cell)

    def end(self):
        self.nb.frontmatter_ = self.fm
        if not self.fm: return
        if not hasattr(self.nb, 'path_'):
            raise AttributeError('Notebook missing `path_` attribute.\n\nPlease remove any nbdev-related notebook filters '
                                 'from your _quarto.yml file (e.g. `ipynb-filter: [nbdev_filter]`), since they are no '
                                 'longer supported as of nbdev v2.3. See the v2.3 launch post for more information: '
                                 'https://forums.fast.ai/t/upcoming-changes-in-v2-3-edit-now-released/98905.')
        self.fm.update({'output-file': _nbpath2html(Path(self.nb.path_)).name})
        _insertfm(self.nb, self.fm)
