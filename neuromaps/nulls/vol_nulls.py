# -*- coding: utf-8 -*-
"""Functionality for running spatial null models."""

def _prep_data(data, atlas, density, parcellation, distmat):
    # if vol, return xyz only
    # if surf, return distance
    # if parcellated, return distance
    # also return type
    pass

def burt2018(data, method="", atlas='fsaverage', density='10k', parcellation=None, # noqa: D103
             n_perm=1000, seed=None, distmat=None, n_proc=1, **kwargs):
    pass

def burt2020(data, method="", atlas='fsaverage', density='10k', parcellation=None, # noqa: D103
             n_perm=1000, seed=None, distmat=None, n_proc=1, **kwargs):
    # options: original sampled, original base, optimized sampled, optimized base
    pass

def moran(data, method="", atlas='fsaverage', density='10k', parcellation=None, # noqa: D103
          n_perm=1000, seed=None, distmat=None, n_proc=1, **kwargs):
    pass