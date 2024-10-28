# -*- coding: utf-8 -*-
"""Functions for statistical analyses."""

from functools import partial

import numpy as np
from scipy import special, stats as sstats
try:
    from scipy.stats._stats_py import _chk2_asarray  # scipy >= 1.8.0
except ImportError:
    from scipy.stats.stats import _chk2_asarray  # scipy < 1.8.0
from sklearn.utils.validation import check_random_state

from neuromaps.images import load_data


def compare_images(src, trg, metric='pearsonr', ignore_zero=True, nulls=None,
                   nan_policy='omit', return_nulls=False):
    """
    Compare images `src` and `trg`.

    If `src` and `trg` represent data from multiple hemispheres the data are
    concatenated across hemispheres prior to comparison

    Parameters
    ----------
    src, trg : tuple or str or os.PathLike or img_like or array-like
        Images (nib.Nifti1Image or nib.GiftiImage) or parcellated data
        to be compared.
    metric : {'pearsonr', 'spearmanr', callable}, optional
        Type of similarity metric to use to compare `src` and `trg` images. If
        a callable function is provided it must accept two inputs and return a
        single value (the similarity metric). Default: 'pearsonr'
    ignore_zero : bool, optional
        Whether to perform comparisons ignoring all zero values in `src` and
        `trg` data. Default: True
    nulls : array_like, optional
        Null data for `src` to use in generating a non-parametric p-value.
        If not specified a parametric p-value is generated. Default: None
    nan_policy : {'propagate', 'raise', 'omit'}, optional
        Defines how to handle when input contains nan. 'propagate' propagates
        the nan values to the callable metric (will return nan if the metric
        is `spearmanr` `or pearsonr`), 'raise' throws an error, 'omit' performs
        the calculations ignoring nan values. Default: 'omit'
    return_nulls : bool, optional
        Whether to return the null distribution of comparisons. Can only be set
        to `True` if `nulls` is not None. Default: False

    Returns
    -------
    similarity : float
         Comparison metric between `src` and `trg`
    pvalue : float
        The p-value of `similarity`, if `nulls` is not None
    nulls : (n_perm, ) array_like
        Null distribution of similarity metrics. Only returned if
        `return_nulls` is True.
    """
    methods = ('pearsonr', 'spearmanr')
    if metric not in methods:
        if not callable(metric):
            raise ValueError(f'Invalid `metric`: {metric}')
        else:
            if not np.isscalar(metric([1, 1], [1, 1])):
                raise ValueError('Provided callable `metric` must accept two '
                                 'inputs and return single value.')

    if return_nulls and nulls is None:
        raise ValueError('`return_nulls` cannot be True when `nulls` is None.')

    srcdata, trgdata = load_data(src), load_data(trg)

    # drop NaNs (if nan_policy==`omit`) and zeros (if ignore_zero=True)
    zeromask = np.zeros(len(srcdata), dtype=bool)
    if ignore_zero:
        zeromask = np.logical_or(np.isclose(srcdata, 0),
                                 np.isclose(trgdata, 0))
    nanmask = np.logical_or(np.isnan(srcdata), np.isnan(trgdata))
    if nan_policy == 'raise':
        if np.any(nanmask):
            raise ValueError('Inputs contain nan')
    elif nan_policy == 'omit':
        mask = np.logical_and(np.logical_not(zeromask),
                              np.logical_not(nanmask))
    elif nan_policy == 'propagate':
        mask = np.logical_not(zeromask)
    srcdata, trgdata = srcdata[mask], trgdata[mask]

    if metric in methods:
        if metric == 'spearmanr':
            srcdata = sstats.rankdata(srcdata)
            trgdata = sstats.rankdata(trgdata)
        metric = partial(efficient_pearsonr, return_pval=False)

    if nulls is not None:
        n_perm = nulls.shape[-1]
        nulls = nulls[mask]
        return permtest_metric(srcdata, trgdata, metric, n_perm=n_perm,
                               nulls=nulls, nan_policy=nan_policy,
                               return_nulls=return_nulls)

    return metric(srcdata, trgdata)


def permtest_metric(a, b, metric='pearsonr', n_perm=1000, seed=0, nulls=None,
                    nan_policy='propagate', return_nulls=False):
    """
    Generate non-parameteric p-value of `a` and `b` for `metric`.

    Calculates two-tailed p-value for hypothesis of whether samples `a` and `b`
    are related using permutation tests

    Parameters
    ----------
    a, b : (N,) array_like
        Sample observations. These arrays must have the same length
    metric : {'pearsonr', 'spearmanr', callable}, optional
        Type of similarity metric to use to compare `a` and `b`. If a callable
        function is provided it must accept two inputs and return a single
        value (the similarity metric). Default: 'pearsonr'
    n_perm : int, optional
        Number of permutations to assess. Unless `a` and `b` are very small
        this will approximate a randomization test via Monte Carlo simulations.
        Default: 1000
    seed : {int, np.random.RandomState instance, None}, optional
        Seed for random number generation. Set to None for pseudo-randomness.
        Default: 0
    nulls : (N, P) array_like, optional
        Null array used in place of shuffled `a` array to compute null
        distribution of correlations. Array must have the same length as `a`
        and `b`. Providing this will override the value supplied to `n_perm`.
        When not specified a standard permutation is used to shuffle `a`.
        Default: None
    nan_policy : {'propagate', 'raise', 'omit'}, optional
        Defines how to handle when inputs contain nan. 'propagate' returns nan,
        'raise' throws an error, 'omit' performs the calculations ignoring nan
        values. Default: 'propagate'
    return_nulls : bool, optional
        Whether to return the null distribution of comparisons. Default: False

    Returns
    -------
    similarity : float
        Similarity metric
    pvalue : float
        Non-parametric p-value
    nulls : (n_perm, ) array_like
        Null distribution of similarity metrics. Only returned if
        `return_nulls` is True.

    Notes
    -----
    The lowest p-value that can be returned by this function is equal to 1 /
    (`n_perm` + 1).
    """

    def nan_wrap(a, b, nan_policy='propagate'):
        nanmask = np.logical_or(np.isnan(a), np.isnan(b))
        if nan_policy == 'raise':
            if np.any(nanmask):
                raise ValueError('Input contains nan')
        elif nan_policy == 'omit':
            a, b = a[~nanmask], b[~nanmask]
        return metric(a, b)

    a, b, _ = _chk2_asarray(a, b, 0)
    rs = check_random_state(seed)

    if len(a) != len(b):
        raise ValueError('Provided arrays do not have same length')

    if a.size == 0 or b.size == 0:
        return np.nan, np.nan

    methods = ('pearsonr', 'spearmanr')
    if metric in methods:
        if metric == 'spearmanr':
            a, b = sstats.rankdata(a), sstats.rankdata(b)
        compfunc = partial(efficient_pearsonr, return_pval=False)
    else:
        compfunc = nan_wrap

    if nulls is not None:
        n_perm = nulls.shape[-1]

    # divide by one forces coercion to float if ndim = 0
    true_sim = compfunc(a, b, nan_policy=nan_policy) / 1
    abs_true = np.abs(true_sim)

    permutations = np.ones(true_sim.shape)
    nulldist = np.zeros(((n_perm, ) + true_sim.shape))
    for perm in range(n_perm):
        # permute `a` and determine whether correlations exceed original
        ap = a[rs.permutation(len(a))] if nulls is None else nulls[:, perm]
        nullcomp = compfunc(ap, b, nan_policy=nan_policy)
        permutations += np.abs(nullcomp) >= abs_true
        nulldist[perm] = nullcomp

    pvals = permutations / (n_perm + 1)  # + 1 in denom accounts for true_sim

    if return_nulls:
        return true_sim, pvals, nulldist

    return true_sim, pvals


def efficient_pearsonr(a, b, ddof=1, nan_policy='propagate', return_pval=True):
    """
    Compute correlation of matching columns in `a` and `b`.

    Parameters
    ----------
    a,b : array_like
        Sample observations. These arrays must have the same length and either
        an equivalent number of columns or be broadcastable
    ddof : int, optional
        Degrees of freedom correction in the calculation of the standard
        deviation. Default: 1
    nan_policy : {'propagate', 'raise', 'omit'}, optional
        Defines how to handle when input contains nan. 'propagate' returns nan,
        'raise' throws an error, 'omit' performs the calculations ignoring nan
        values. Default: 'propagate'

    Returns
    -------
    corr : float or numpy.ndarray
        Pearson's correlation coefficient between matching columns of inputs
    pval : float or numpy.ndarray
        Two-tailed p-values. Only returned if `return_pval` is True

    Notes
    -----
    If either input contains nan and nan_policy is set to 'omit', both arrays
    will be masked to omit the nan entries.
    """
    a, b, _ = _chk2_asarray(a, b, 0)
    if len(a) != len(b):
        raise ValueError('Provided arrays do not have same length')

    if a.size == 0 or b.size == 0:
        return np.nan, np.nan

    if nan_policy not in ('propagate', 'raise', 'omit'):
        raise ValueError(f'Value for nan_policy "{nan_policy}" not allowed')

    a, b = a.reshape(len(a), -1), b.reshape(len(b), -1)
    if (a.shape[1] != b.shape[1]):
        a, b = np.broadcast_arrays(a, b)

    mask = np.logical_or(np.isnan(a), np.isnan(b))
    if nan_policy == 'raise' and np.any(mask):
        raise ValueError('Input contains nan')
    elif nan_policy == 'omit':
        # avoid making copies of the data, if possible
        a = np.ma.masked_array(a, mask, copy=False, fill_value=np.nan)
        b = np.ma.masked_array(b, mask, copy=False, fill_value=np.nan)

    with np.errstate(invalid='ignore'):
        corr = (sstats.zscore(a, ddof=ddof, nan_policy=nan_policy)
                * sstats.zscore(b, ddof=ddof, nan_policy=nan_policy))

    sumfunc, n_obs = np.sum, len(a)
    if nan_policy == 'omit':
        corr = corr.filled(np.nan)
        sumfunc = np.nansum
        n_obs = np.squeeze(np.sum(np.logical_not(np.isnan(corr)), axis=0))

    corr = sumfunc(corr, axis=0) / (n_obs - 1)
    corr = np.squeeze(np.clip(corr, -1, 1)) / 1

    if return_pval:
        # taken from scipy.stats
        ab = (n_obs / 2) - 1
        prob = 2 * special.betainc(ab, ab, 0.5 * (1 - np.abs(corr)))

        return corr, prob

    return corr


def _sw_nest_enrich_score(L, network_ind, one_sided=True):
    """
    Calculate the network enrichment score for a given statistic.

    Parameters
    ----------
    L : array_like, shape (n_vertices,)
        Statistics
    network_ind : array_like, shape (n_vertices,)
        Network indicator, where 1 indicates membership in the network of
        interest and 0 otherwise.
    one_sided : bool, optional
        Whether to perform a one-sided test. Default: True

    Returns
    -------
    enrich_score : float
        Network enrichment score
    """
    L_order = np.argsort(L)[::-1]
    L_sorted = L[L_order]
    network_ind_sorted = network_ind[L_order]

    if one_sided:
        L_sorted_abs = np.abs(L_sorted)
        P_hit_numerator = np.cumsum(L_sorted_abs * network_ind_sorted)
    else:
        P_hit_numerator = np.cumsum(network_ind_sorted)
    P_hit = P_hit_numerator / P_hit_numerator[-1]

    P_miss_numerator = np.cumsum(1 - network_ind_sorted)
    P_miss = P_miss_numerator / P_miss_numerator[-1]

    running_sum = P_hit - P_miss
    enrich_score = np.max(np.abs(running_sum))

    return enrich_score


def sw_nest(stat_emp, stat_perm, network_ind, one_sided=True):
    """
    Network Enrichment Significance Testing (NEST) from Weinstein et al., 2024.

    Check `original implementation <https://github.com/smweinst/NEST>`_ for more
    details.

    Parameters
    ----------
    stat_emp : array_like, shape (n_vertices,)
        Empirical statistics
    stat_perm : array_like, shape (n_permutations, n_vertices)
        Permuted statistics. Each row corresponds to a permutation calculated by
        permuting the subjects and re-estimating the statistic.
    network_ind : array_like, shape (n_vertices,)
        Network indicator, where 1 indicates membership in the network of
        interest and 0 otherwise.
    one_sided : bool, optional
        Whether to perform a one-sided test. Default: True

    Returns
    -------
    p : float
        Significance level

    References
    ----------
    .. [1] Weinstein, S. M., Vandekar, S. N., Li, B., Alexander-Bloch, A. F.,
       Raznahan, A., Li, M., Gur, R. E., Gur, R. C., Roalf, D. R., Park, M. T.
       M., Chakravarty, M., Baller, E. B., Linn, K. A., Satterthwaite, T. D., &
       Shinohara, R. T. (2024). Network enrichment significance testing in
       brain-phenotype association studies. Human Brain Mapping, 45(8), e26714.
       https://doi.org/10.1002/hbm.26714

    """
    es_emp = _sw_nest_enrich_score(stat_emp, network_ind, one_sided=one_sided)
    es_perm = np.array([
        _sw_nest_enrich_score(s, network_ind, one_sided=one_sided) for s in stat_perm
    ])
    return (1 + np.sum(es_perm > es_emp)) / (1 + len(es_perm))
