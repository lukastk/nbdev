# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06_merge.ipynb.

# %% auto 0
__all__ = ['conf_re', 'unpatch', 'nbprocess_fix']

# %% ../nbs/06_merge.ipynb 3
from .imports import *
from .read import *
from .export import *
from .sync import *
from fastcore.script import *

from difflib import SequenceMatcher
import json,shutil

# %% ../nbs/06_merge.ipynb 17
_BEG,_MID,_END = '<'*7,'='*7,'>'*7
conf_re = re.compile(rf'^{_BEG}\s+(\S+)\n(.*?)\n{_MID}\n(.*?)^{_END}\s+(\S+)\n', re.MULTILINE|re.DOTALL)

def _unpatch_f(before, cb1, cb2, c, r):
    if cb1 is not None and cb1 != cb2: raise Exception(f'Branch mismatch: {cb1}/{cb2}')
    r.append(before)
    r.append(c)
    return cb2

# %% ../nbs/06_merge.ipynb 18
def unpatch(s:str):
    "Takes a string with conflict markers and returns the two original files, and their branch names"
    *main,last = conf_re.split(s)
    r1,r2,c1b,c2b = [],[],None,None
    for before,c1_branch,c1,c2,c2_branch in chunked(main, 5):
        c1b = _unpatch_f(before, c1b, c1_branch, c1, r1)
        c2b = _unpatch_f(before, c2b, c2_branch, c2, r2)
    return ''.join(r1+[last]), ''.join(r2+[last]), c1b, c2b

# %% ../nbs/06_merge.ipynb 23
def _make_md(code): return [dict(source=f'`{code}`', cell_type="markdown", metadata={})]
def _make_conflict(a,b, branch1, branch2):
    return _make_md(f'{_BEG} {branch1}') + a+_make_md(_MID)+b + _make_md(f'{_END} {branch2}')

def _merge_cells(a, b, brancha, branchb, theirs):
    matches = SequenceMatcher(None, a, b).get_matching_blocks()
    res,prev_sa,prev_sb,conflict = [],0,0,False
    for sa,sb,sz in matches:
        ca,cb = a[prev_sa:sa],b[prev_sb:sb]
        if ca or cb:
            res += _make_conflict(ca, cb, brancha, branchb)
            conflict = True
        if sz: res += b[sb:sb+sz] if theirs else a[sa:sa+sz]
        prev_sa,prev_sb = sa+sz,sb+sz
    return res,conflict

# %% ../nbs/06_merge.ipynb 24
@call_parse
def nbprocess_fix(nbname:str, # notebook filename to fix
              outname:str=None, # filename of output notebook, defaults to `nbname`
              nobackup:bool=True, # do not backup `nbname` to `nbname.bak` if `outname` not provided
              theirs:bool=False, # use their outputs/metadata instead of ours
              noprint:bool=False): # Do not print info about whether conflict found
    "Create working notebook from conflicted notebook `nbname`"
    nbname = Path(nbname)
    if not nobackup and not outname: shutil.copy(nbname, nbname.with_suffix('.ipynb.bak'))
    nbtxt = nbname.read_text()
    a,b,branch1,branch2 = unpatch(nbtxt)
    ac,bc = dict2nb(json.loads(a)),dict2nb(json.loads(b))
    dest = bc if theirs else ac
    cells,conflict = _merge_cells(ac.cells, bc.cells, branch1, branch2, theirs=theirs)
    dest.cells = cells
    write_nb(dest, ifnone(outname, nbname))
    if not noprint:
        if conflict: print("One or more conflict remains in the notebook, please inspect manually.")
        else: print("Successfully merged conflicts!")
    return conflict
