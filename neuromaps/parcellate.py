# -*- coding: utf-8 -*-
"""Functionality for parcellating data."""

import nibabel as nib
<<<<<<< HEAD
from nilearn.maskers import NiftiLabelsMasker
=======
try:
    from nilearn.maskers import NiftiLabelsMasker
except:
    from nilearn.input_data import NiftiLabelsMasker
>>>>>>> 276cdaf ([FIX] Fix deprecations)
from nilearn.image import new_img_like
from nilearn.masking import compute_background_mask
import numpy as np

from neuromaps.datasets import ALIAS, DENSITIES, fetch_atlas
from neuromaps.images import construct_shape_gii, load_gifti, load_data
from neuromaps.resampling import resample_images
from neuromaps.transforms import _check_hemi, _estimate_density
from neuromaps.nulls.spins import vertices_to_parcels, parcels_to_vertices


def _gifti_to_array(gifti):
    """Convert tuple of `gifti` to numpy array."""
    return np.hstack([load_gifti(img).agg_data() for img in gifti])


def _array_to_gifti(data):
    """Convert numpy `array` to tuple of gifti images."""
    return tuple(construct_shape_gii(arr) for arr in np.split(data, 2))


class Parcellater():
    """
    Class for parcellating arbitrary volumetric / surface data.

    Parameters
    ----------
    parcellation : str or os.PathLike or Nifti1Image or GiftiImage or tuple
        Parcellation image or surfaces, where each region is identified by a
        unique integer ID. All regions with an ID of 0 are ignored.
    space : str
        The space in which `parcellation` is defined
    resampling_target : {'data', 'parcellation', None}, optional
        Gives which image gives the final shape/size. For example, if
        `resampling_target` is 'data', the `parcellation` is resampled to the
        space + resolution of the data, if needed. If it is 'parcellation' then
        any data provided to `.fit()` are transformed to the space + resolution
        of `parcellation`. Providing None means no resampling; if spaces +
        resolutions of the `parcellation` and data provided to `.fit()` do not
        match a ValueError is raised. Default: 'data'
    hemi : {'L', 'R'}, optional
        If provided `parcellation` represents only one hemisphere of a surface
        atlas then this specifies which hemisphere. If not specified it is
        assumed that `parcellation` is (L, R) hemisphere. Ignored if `space` is
        'MNI152'. Default: None
    """

    def __init__(self, parcellation, space, resampling_target='data',
                 hemi=None):
        self.parcellation = parcellation
        self.space = ALIAS.get(space, space)
        self.resampling_target = resampling_target
        self.hemi = hemi
        self._volumetric = self.space == 'MNI152'

        if self.resampling_target == 'parcellation':
            self._resampling = 'transform_to_trg'
        else:
            self._resampling = 'transform_to_src'

        if not self._volumetric:
            self.parcellation, self.hemi = zip(
                *_check_hemi(self.parcellation, self.hemi)
            )

        if self.resampling_target not in ('parcellation', 'data', None):
            raise ValueError('Invalid value for `resampling_target`: '
                             f'{resampling_target}')

        if self.space not in DENSITIES:
            raise ValueError(f'Invalid value for `space`: {space}')

    def fit(self):
        """Prepare parcellation for data extraction."""
        if not self._volumetric:
            self.parcellation = tuple(
                load_gifti(img) for img in self.parcellation
            )
        self._fit = True
        return self

    def transform(self, data, space, ignore_background_data=False,
                  background_value=None, hemi=None):
        """
        Apply parcellation to `data` in `space`.

        Parameters
        ----------
        data : str or os.PathLike or Nifti1Image or GiftiImage or tuple
            Data to parcellate
        space : str
            The space in which `data` is defined
        hemi : {'L', 'R'}, optional
            If provided `data` represents only one hemisphere of a surface
            dataset then this specifies which hemisphere. If not specified it
            is assumed that `data` is (L, R) hemisphere. Ignored if `space` is
            'MNI152'. Default: None
        ignore_background_data: bool
            Specifies whether the background data values should be ignored
            when computing the average `data` within each parcel. If set to
            True and `background_value` is set to None, the background_value is
            estimated from the data: if there are NaNs in the data, the
            background value is set to NaN. Otherwise, it is estimated as
            the median of the values on the border of the images for
            volumetric images or as the median of the values within the medial
            wall for surface images. The background value can also be set
            manually using the `background_value` parameter. Default: False
        background_value: float
            Specifies the background value to ignore when computing the
            averages and when `ignore_background_data` is True.
            Default: None

        Returns
        -------
        parcellated : np.ndarray
            Parcellated `data`
        """
        self._check_fitted()

        space = ALIAS.get(space, space)
        if (self.resampling_target == 'data' and space == 'MNI152'
                and not self._volumetric):
            raise ValueError('Cannot use resampling_target="data" when '
                             'provided parcellation is in surface space and '
                             'provided data are in MNI152 space.')
        elif (self.resampling_target == 'parcellation' and self._volumetric
                and space != 'MNI152'):
            raise ValueError('Cannot use resampling_target="parcellation" '
                             'when provided parcellation is in MNI152 space '
                             'and provided data are in surface space.')

        if hemi is not None and hemi not in self.hemi:
            raise ValueError('Cannot parcellate data from {hemi} hemisphere '
                             'when parcellation was provided for incompatible '
                             'hemisphere: {self.hemi}')

        if isinstance(data, np.ndarray):
            if space == 'MNI152':
                raise ValueError('Volumetric data to be parcellated should be '
                                 'provided as a Nifti1Image with the correct '
                                 'affine defined. You can use '
                                 'nibabel.nifti1.Nifti1Image to construct a '
                                 'Nifti1Image from your array.')
            else:
                data = _array_to_gifti(data)
        if self.resampling_target in ('data', None):
            resampling_method = 'nearest'
        else:
            resampling_method = 'linear'
        data, parc = resample_images(data, self.parcellation,
                                     space, self.space, hemi=hemi,
                                     resampling=self._resampling,
                                     method=resampling_method)

        if ((self.resampling_target == 'data'
             and space.lower() == 'mni152')
                or (self.resampling_target == 'parcellation'
                    and self._volumetric)):
            data = nib.concat_images([nib.squeeze_image(data)])
            if ignore_background_data:
                if background_value is None:
                    mask_img = compute_background_mask(data)
                else:
                    mask_img = new_img_like(
                        data, data.get_fdata() != background_value)
            else:
                mask_img = None
            parcellated = NiftiLabelsMasker(
                parc, mask_img=mask_img, resampling_target=None
            ).fit_transform(data)
        else:
            if not self._volumetric:
                for n, _ in enumerate(parc):
                    parc[n].labeltable.labels = \
                        self.parcellation[n].labeltable.labels
            darr = _gifti_to_array(data)
            if ignore_background_data and background_value is None:
                density, = _estimate_density((data,), hemi=hemi)
                if self.resampling_target in ('data', None):
                    mask_space = space
                elif self.resampling_target == 'parcellation':
                    mask_space = self.space
                nomedialwall = load_data(
                    fetch_atlas(mask_space, density)['medial'])
                background_value = np.median(darr[nomedialwall == 0])
            parcellated = vertices_to_parcels(
                darr, parc, background=background_value)

        return parcellated

    def inverse_transform(self, data):
        """
        Project `data` to space + density of parcellation.

        Parameters
        ----------
        data : array_like
            Parcellated data to be projected to the space of parcellation

        Returns
        -------
        data : Nifti1Image or tuple-of-nib.GiftiImage
            Provided `data` in space + resolution of parcellation
        """
        if not self._volumetric:
            verts = parcels_to_vertices(data, self.parcellation)
            img = _array_to_gifti(verts)
        else:
            data = np.atleast_2d(data)
            img = NiftiLabelsMasker(self.parcellation).fit() \
                                                      .inverse_transform(data)
        return img

    def fit_transform(self, data, space, ignore_background_data=False,
                      background_value=None, hemi=None):
        """Prepare and perform parcellation of `data`."""
        return self.fit().transform(data, space, ignore_background_data,
                                    background_value, hemi)

    def _check_fitted(self):
        """Check if Parcellater has been fit."""
        if not hasattr(self, '_fit'):
            raise ValueError(f'It seems that {self.__class__.__name__} has '
                             'not been fit. You must call `.fit()` before '
                             'calling `.transform()`')
