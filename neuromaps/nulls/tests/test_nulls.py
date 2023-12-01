# -*- coding: utf-8 -*-
"""For testing neuromaps.nulls.nulls functionality."""

import pytest
from neuromaps.nulls.nulls import (
    alexander_bloch, vasa, hungarian, baum, cornblath
)
from neuromaps.datasets import fetch_annotation
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
    """Fixture for surface annotation."""
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
    """Fixture for volume annotation."""
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
    """Fixture for parcellated surface annotation."""
    surf_tuple, annot = sample_surface
    source, desc, space, den = surf_tuple

    if request.param[0].startswith("schaefer"):
        parc_name, parc_fetcher, parc_label = request.param
        if space == "fsaverage":
            if den == "164k":
                atlas = annot_to_gifti(parc_fetcher(version="fsaverage")[parc_label])
            elif den == "41k":
                atlas = annot_to_gifti(parc_fetcher(version="fsaverage6")[parc_label])
            elif den == "10k":
                atlas = annot_to_gifti(parc_fetcher(version="fsaverage5")[parc_label])
            else:
                raise NotImplementedError(
                    f"Invalid surface density: {den} for fsaverage space"
                )
        elif space == "fsLR":
            atlas = dlabel_to_gifti(parc_fetcher(version="fslr32k")[parc_label])
        else:
            raise NotImplementedError(f"Invalid surface space: {space}")
        parc = Parcellater(atlas, space)
    else:
        raise NotImplementedError(f"Invalid parcellation: {request.param[0]}")

    annot_parc = parc.fit_transform(annot, space)

    return surf_tuple, parc_name, atlas, annot_parc


@pytest.fixture(
    scope="module", 
    params=sample_volume_parcellations, 
    ids=[_[0] for _ in sample_volume_parcellations]
)
def sample_volume_parcellated(sample_volume, request):
    """Fixture for parcellated volume annotation."""
    vol_tuple, annot = sample_volume
    source, desc, space, res = vol_tuple

    if request.param[0].startswith("lausanne"):
        parc_name, parc_fetcher, parc_label = request.param
        atlas = parc_fetcher(version="MNI152NLin2009aSym")[parc_label]
        parc = Parcellater(atlas, space)
    else:
        raise NotImplementedError(f"Invalid parcellation: {request.param[0]}")

    annot_parc = parc.fit_transform(annot, space)

    return vol_tuple, parc_name, atlas, annot_parc

class TestFixturesSmoke:
    """Test fixtures for null models."""

    def test_fixture_surface_smoke(self, sample_surface):
        """Test fetching surface annotation."""
        print(sample_surface[0])
        assert True


    def test_fixture_volume_smoke(self, sample_volume):
        """Test fetching volume annotation."""
        print(sample_volume[0])
        assert True


    def test_fixture_surface_parcellated_smoke(self, sample_surface_parcellated):
        """Test fetching parcellated surface annotation."""
        surf_tuple, parc_name, atlas, annot_parc = sample_surface_parcellated
        print(surf_tuple, parc_name, atlas, annot_parc.shape[0])
        assert True

    
    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # nilearn/nilearn/pull/3722
        )
    def test_fixture_volume_parcellated_smoke(self, sample_volume_parcellated):
        """Test fetching parcellated volume annotation."""
        vol_tuple, parc_name, atlas, annot_parc = sample_volume_parcellated
        print(vol_tuple, parc_name, atlas, annot_parc.shape[0])
        assert True

class TestAlexanderBloch:
    """Test alexander-bloch null model."""

    def test_alexander_bloch_surface(self, sample_surface):
        """Test alexander-bloch null model for surface."""
        surf_tuple, annot = sample_surface
        _, _, space, den = surf_tuple
        alexander_bloch(annot, atlas=space, density=den, n_perm=3)


    @pytest.mark.xfail
    def test_alexander_bloch_volume(self, sample_volume):
        """Test alexander-bloch null model for volume."""
        vol_tuple, annot = sample_volume
        _, _, space, res = vol_tuple
        alexander_bloch(annot, atlas=space, density=res, n_perm=3)


    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # nilearn/nilearn/pull/3722
        )
    def test_alexander_bloch_surface_parcellated(self, sample_surface_parcellated):
        """Test alexander-bloch null model for parcellated surface."""
        surf_tuple, parc_name, atlas, annot_parc = sample_surface_parcellated
        _, _, space, den = surf_tuple
        print(surf_tuple, parc_name, atlas, annot_parc.shape)

        alexander_bloch(
            annot_parc, atlas=space, density=den, parcellation=atlas, n_perm=3
        )


    @pytest.mark.xfail
    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # neuromaps.images.load_data()
        )
    def test_alexander_bloch_volume_parcellated(self, sample_volume_parcellated):
        """Test alexander-bloch null model for parcellated volume."""
        vol_tuple, parc_name, atlas, annot_parc = sample_volume_parcellated
        _, _, space, res = vol_tuple
        print(vol_tuple, parc_name, atlas, annot_parc.shape)

        alexander_bloch(
            annot_parc, atlas=space, density=res, parcellation=atlas, n_perm=3
        )

class TestVasa:
    """Test vasa null model."""

    @pytest.mark.xfail
    def test_vasa_surface(self, sample_surface):
        """Test vasa null model for surface."""
        surf_tuple, annot = sample_surface
        _, _, space, den = surf_tuple
        vasa(annot, atlas=space, density=den, n_perm=3)


    @pytest.mark.xfail
    def test_vasa_volume(self, sample_volume):
        """Test vasa null model for volume."""
        vol_tuple, annot = sample_volume
        _, _, space, res = vol_tuple
        vasa(annot, atlas=space, density=res, n_perm=3)


    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # nilearn/nilearn/pull/3722
        )
    def test_vasa_surface_parcellated(self, sample_surface_parcellated):
        """Test vasa null model for parcellated surface."""
        surf_tuple, parc_name, atlas, annot_parc = sample_surface_parcellated
        _, _, space, den = surf_tuple
        print(surf_tuple, parc_name, atlas, annot_parc.shape)

        vasa(
            annot_parc, atlas=space, density=den, parcellation=atlas, n_perm=3
        )


    @pytest.mark.xfail
    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # neuromaps.images.load_data()
        )
    def test_vasa_volume_parcellated(self, sample_volume_parcellated):
        """Test vasa null model for parcellated volume."""
        vol_tuple, parc_name, atlas, annot_parc = sample_volume_parcellated
        _, _, space, res = vol_tuple
        print(vol_tuple, parc_name, atlas, annot_parc.shape)

        vasa(
            annot_parc, atlas=space, density=res, parcellation=atlas, n_perm=3
        )

class TestHungarian:
    """Test hungarian null model."""

    @pytest.mark.xfail
    def test_hungarian_surface(self, sample_surface):
        """Test hungarian null model for surface."""
        surf_tuple, annot = sample_surface
        _, _, space, den = surf_tuple
        hungarian(annot, atlas=space, density=den, n_perm=3)


    @pytest.mark.xfail
    def test_hungarian_volume(self, sample_volume):
        """Test hungarian null model for volume."""
        vol_tuple, annot = sample_volume
        _, _, space, res = vol_tuple
        hungarian(annot, atlas=space, density=res, n_perm=3)


    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # nilearn/nilearn/pull/3722
        )
    def test_hungarian_surface_parcellated(self, sample_surface_parcellated):
        """Test hungarian null model for parcellated surface."""
        surf_tuple, parc_name, atlas, annot_parc = sample_surface_parcellated
        _, _, space, den = surf_tuple
        print(surf_tuple, parc_name, atlas, annot_parc.shape)

        hungarian(
            annot_parc, atlas=space, density=den, parcellation=atlas, n_perm=3
        )


    @pytest.mark.xfail
    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # neuromaps.images.load_data()
        )
    def test_hungarian_volume_parcellated(self, sample_volume_parcellated):
        """Test hungarian null model for parcellated volume."""
        vol_tuple, parc_name, atlas, annot_parc = sample_volume_parcellated
        _, _, space, res = vol_tuple
        print(vol_tuple, parc_name, atlas, annot_parc.shape)

        hungarian(
            annot_parc, atlas=space, density=res, parcellation=atlas, n_perm=3
        )

class TestBaum:
    """Test baum null model."""

    @pytest.mark.xfail
    def test_baum_surface(self, sample_surface):
        """Test baum null model for surface."""
        surf_tuple, annot = sample_surface
        _, _, space, den = surf_tuple
        baum(annot, atlas=space, density=den, n_perm=3)


    @pytest.mark.xfail
    def test_baum_volume(self, sample_volume):
        """Test baum null model for volume."""
        vol_tuple, annot = sample_volume
        _, _, space, res = vol_tuple
        baum(annot, atlas=space, density=res, n_perm=3)


    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # nilearn/nilearn/pull/3722
        )
    def test_baum_surface_parcellated(self, sample_surface_parcellated):
        """Test baum null model for parcellated surface."""
        surf_tuple, parc_name, atlas, annot_parc = sample_surface_parcellated
        _, _, space, den = surf_tuple
        print(surf_tuple, parc_name, atlas, annot_parc.shape)

        baum(
            annot_parc, atlas=space, density=den, parcellation=atlas, n_perm=3
        )


    @pytest.mark.xfail
    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # neuromaps.images.load_data()
        )
    def test_baum_volume_parcellated(self, sample_volume_parcellated):
        """Test baum null model for parcellated volume."""
        vol_tuple, parc_name, atlas, annot_parc = sample_volume_parcellated
        _, _, space, res = vol_tuple
        print(vol_tuple, parc_name, atlas, annot_parc.shape)

        baum(
            annot_parc, atlas=space, density=res, parcellation=atlas, n_perm=3
        )

class TestCornblath:
    """Test cornblath null model."""

    @pytest.mark.xfail
    def test_cornblath_surface(self, sample_surface):
        """Test cornblath null model for surface."""
        surf_tuple, annot = sample_surface
        _, _, space, den = surf_tuple
        cornblath(annot, atlas=space, density=den, n_perm=3)


    @pytest.mark.xfail
    def test_cornblath_volume(self, sample_volume):
        """Test cornblath null model for volume."""
        vol_tuple, annot = sample_volume
        _, _, space, res = vol_tuple
        cornblath(annot, atlas=space, density=res, n_perm=3)


    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # nilearn/nilearn/pull/3722
        )
    def test_cornblathsurface_parcellated(self, sample_surface_parcellated):
        """Test cornblath null model for parcellated surface."""
        surf_tuple, parc_name, atlas, annot_parc = sample_surface_parcellated
        _, _, space, den = surf_tuple
        print(surf_tuple, parc_name, atlas, annot_parc.shape)

        cornblath(
            annot_parc, atlas=space, density=den, parcellation=atlas, n_perm=3
        )


    @pytest.mark.xfail
    @pytest.mark.filterwarnings(
            "ignore::DeprecationWarning" # neuromaps.images.load_data()
        )
    def test_cornblath_volume_parcellated(self, sample_volume_parcellated):
        """Test cornblath null model for parcellated volume."""
        vol_tuple, parc_name, atlas, annot_parc = sample_volume_parcellated
        _, _, space, res = vol_tuple
        print(vol_tuple, parc_name, atlas, annot_parc.shape)

        cornblath(
            annot_parc, atlas=space, density=res, parcellation=atlas, n_perm=3
        )


@pytest.mark.xfail
def test__get_distmat():
    """Test getting distance matrix."""
    assert False


@pytest.mark.xfail
def test__make_surrogates():
    """Test making surrogates."""
    assert False

class TestBurt2018:
    """Test burt2018 null model."""

    @pytest.mark.xfail
    def test_burt2018(self):
        """Test burt2018 null model."""
        assert False

class TestBurt2020:
    """Test burt2020 null model."""

    @pytest.mark.xfail
    def test_burt2020(self):
        """Test burt2020 null model."""
        assert False


class TestMoran:
    """Test moran null model."""

    @pytest.mark.xfail
    def test_moran(self):
        """Test moran null model."""
        assert False
