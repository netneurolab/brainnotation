# -*- coding: utf-8 -*-
"""For testing neuromaps.nulls.nulls functionality."""

import pytest
from neuromaps.datasets import fetch_annotation, available_annotations
from neuromaps.parcellate import Parcellater
from neuromaps.images import annot_to_gifti, dlabel_to_gifti
from netneurotools.datasets import fetch_schaefer2018, fetch_cammoun2012

sample_surface_maps = [
    ('abagen', 'genepc1', 'fsaverage', '10k'),
    ('hcps1200', 'myelinmap', 'fsLR', '32k'),
]
sample_volume_maps = [
    ('neurosynth', 'cogpc1', 'MNI152', '2mm'),
    ('dukart2018', 'flumazenil', 'MNI152', '3mm'),
]

sample_surface_parcellations = [
    ("schaefer100x7", fetch_schaefer2018, '100Parcels7Networks'),
    ("schaefer200x7", fetch_schaefer2018, '200Parcels7Networks')
]

sample_volume_parcellations = [
    ("lausanne033", fetch_cammoun2012, 'scale033'),
    ("lausanne060", fetch_cammoun2012, 'scale060')
]

@pytest.fixture(
    scope="module", 
    params=sample_surface_maps, 
    ids=["_".join(_) for _ in sample_surface_maps]
)
def sample_surface(request):
    source, desc, space, den = request.param
    annot = fetch_annotation(
        source=source, desc=desc, space=space, den=den
    )
    return request.param, annot

@pytest.fixture(
    scope="module", 
    params=sample_volume_maps, 
    ids=["_".join(_) for _ in sample_volume_maps]
)
def sample_volume(request):
    source, desc, space, res = request.param
    annot = fetch_annotation(
        source=source, desc=desc, space=space, res=res
    )
    return request.param, annot

@pytest.fixture(
    scope="module", 
    params=sample_surface_parcellations, 
    ids=[_[0] for _ in sample_surface_parcellations]
)
def sample_surface_parcellated(sample_surface, request):
    surf_tuple, annot = sample_surface
    source, desc, space, den = surf_tuple

    if request.param[0].startswith("schaefer"):
        parc_name, parc_fetcher, parc_label = request.param
        if space == "fsaverage":
            atlas = annot_to_gifti(parc_fetcher(version="fsaverage")[parc_label])
        elif space == "fsLR":
            atlas = dlabel_to_gifti(parc_fetcher(version="fslr32k")[parc_label])
        else:
            raise NotImplementedError(f"Invalid surface space: {space}")
        parc = Parcellater(atlas, space)
    else:
        raise NotImplementedError(f"Invalid parcellation: {request.param[0]}")

    annot_parc = parc.fit_transform(annot, space)

    return surf_tuple, parc_name, annot_parc


@pytest.fixture(
    scope="module", 
    params=sample_volume_parcellations, 
    ids=[_[0] for _ in sample_volume_parcellations]
)
def sample_volume_parcellated(sample_volume, request):
    vol_tuple, annot = sample_volume
    source, desc, space, res = vol_tuple

    if request.param[0].startswith("lausanne"):
        parc_name, parc_fetcher, parc_label = request.param
        atlas = parc_fetcher(version="MNI152NLin2009aSym")[parc_label]
        parc = Parcellater(atlas, space)
    else:
        raise NotImplementedError(f"Invalid parcellation: {request.param[0]}")

    annot_parc = parc.fit_transform(annot, space)

    return vol_tuple, parc_name, annot_parc


def test_fixture_surface_smoke(sample_surface):
    # print(sample_surface[0])
    pass

def test_fixture_volume_smoke(sample_volume):
    # print(sample_volume[0])
    pass

# def test_fixture_surface_parcellated_smoke(sample_surface, sample_parcellation):
#     print(sample_surface[0], sample_parcellation)

# def test_fixture_volume_parcellated_smoke(sample_volume, sample_parcellation):
#     print(sample_volume[0], sample_parcellation)


def test_fixture_surface_parcellated_smoke(sample_surface_parcellated):
    surf_tuple, parc_name, annot_parc = sample_surface_parcellated
    # print(surf_tuple, parc_name, annot_parc.shape[0])
    pass

def test_fixture_volume_parcellated_smoke(sample_volume_parcellated):
    vol_tuple, parc_name, annot_parc = sample_volume_parcellated
    # print(vol_tuple, parc_name, annot_parc.shape[0])
    pass


@pytest.mark.xfail
def test_alexander_bloch(sample_surface):
    """Test alexander-bloch null model."""
    assert False

@pytest.mark.xfail
def test_alexander_bloch_parcellated(sample_surface, sample_parcellation):
    """Test alexander-bloch null model for parcellated maps."""
    assert False


@pytest.mark.xfail
def test_vasa():
    """Test vasa null model."""
    assert False

@pytest.mark.xfail
def test_vasa_parcellated():
    """Test vasa null model for parcellated maps."""
    assert False


@pytest.mark.xfail
def test_hungarian():
    """Test hungarian null model."""
    assert False

@pytest.mark.xfail
def test_hungarian_parcellated():
    """Test hungarian null model for parcellated maps."""
    assert False

@pytest.mark.xfail
def test_baum():
    """Test baum null model."""
    assert False


@pytest.mark.xfail
def test_cornblath():
    """Test cornblath null model."""
    assert False


@pytest.mark.xfail
def test__get_distmat():
    """Test getting distance matrix."""
    assert False


@pytest.mark.xfail
def test__make_surrogates():
    """Test making surrogates."""
    assert False


@pytest.mark.xfail
def test_burt2018():
    """Test burt2018 null model."""
    assert False


@pytest.mark.xfail
def test_burt2020():
    """Test burt2020 null model."""
    assert False


@pytest.mark.xfail
def test_moran():
    """Test moran null model."""
    assert False
