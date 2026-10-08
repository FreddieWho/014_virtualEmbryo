import importlib.util
from pathlib import Path
import numpy as np
import pytest
p=Path(__file__).resolve().parents[1]/'code/validation.py'
s=importlib.util.spec_from_file_location('validation',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)

def test_heldout_response_mutation_cannot_change_sd():
 y={'a':np.array([1.,2.]),'b':np.array([3.,6.]),'q':np.array([1e8,-1e8])}
 before=v.training_response_sd(y,['a','b'],'q');y['q']*=1e20
 np.testing.assert_array_equal(before,v.training_response_sd(y,['a','b'],'q'))
 with pytest.raises(ValueError):v.training_response_sd(y,['a','q'],'q')

def test_donor_excludes_heldout_and_has_no_outcome_input():
 E=np.array([[1.,0.],[.2,.8],[.9,.1]])
 assert v.nearest_training_donor(E,['q','a','b'],['a','b'],'q')=='b'
 with pytest.raises(ValueError):v.nearest_training_donor(E,['q','a','b'],['q','a'],'q')

def test_signed_program_reverses_with_response():
 H=np.array([[4.,3.,0.,0.],[0.,0.,3.,4.]])
 d=H[1]-H[0]
 assert v.signed_program_pair(H,d)==(0,1)
 assert v.signed_program_pair(H,-d)==(1,0)
 assert v.signed_program_pair(H,np.zeros(4))==(None,None)
 remove,add=v.signed_program_pair(H[:1],d)
 assert remove==0 and add is None

def test_program_swap_moves_with_requested_direction():
 H=np.array([[4.,3.,0.,0.],[0.,0.,3.,4.]])
 W=np.array([[1.,1.],[2.,2.]])
 raw=W@H;d=H[1]-H[0];remove,add=v.signed_program_pair(H,d)
 r=W[:,remove,None]*H[remove];a=W[:,add,None]*H[add]
 changed=raw-.25*r+.25*(r.sum(1)/a.sum(1))[:,None]*a
 assert (changed.mean(0)-raw.mean(0))@d>0
