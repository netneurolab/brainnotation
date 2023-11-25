# -*- coding: utf-8 -*-
"""Utilities for loading / creating datasets."""

import json
import os
try:
    import importlib.resources
    _importlib_avail = True
except ImportError:
    from pkg_resources import resource_filename
    _importlib_avail = False

import requests

RESTRICTED = ["grh4d"]


def _osfify_urls(data, return_restricted=True):
    """
    Format `data` object with OSF API URL.

    Parameters
    ----------
    data : object
        If dict with a `url` key, will format OSF_API with relevant values
    return_restricted : bool, optional
        Whether to return restricted annotations. These will only be accessible
        with a valid OSF token. Default: True

    Returns
    -------
    data : object
        Input data with all `url` dict keys formatted
    """
    OSF_API = "https://files.osf.io/v1/resources/{}/providers/osfstorage/{}"

    if isinstance(data, str) or data is None:
        return data
    elif 'url' in data:
        # if url is None then we this is a malformed entry and we should ignore
        if data['url'] is None:
            return
        # if the url isn't a string assume we're supposed to format it
        elif not isinstance(data['url'], str):
            if data['url'][0] in RESTRICTED and not return_restricted:
                return
            data['url'] = OSF_API.format(*data['url'])

    try:
        for key, value in data.items():
            data[key] = _osfify_urls(value, return_restricted)
    except AttributeError:
        for n, value in enumerate(data):
            data[n] = _osfify_urls(value, return_restricted)
        # drop the invalid entries
        data = [d for d in data if d is not None]

    return data


def get_dataset_info(name, return_restricted=True):
    """
    Return information for requested dataset `name`.

    Parameters
    ----------
    name : str
        Name of dataset
    return_restricted : bool, optional
        Whether to return restricted annotations. These will only be accessible
        with a valid OSF token. Default: True

    Returns
    -------
    dataset : dict or list-of-dict
        Information on requested data
    """
    if _importlib_avail:
        fn = importlib.resources.files("neuromaps") / "datasets/data/osf.json"
    else:
        fn = resource_filename(
            'neuromaps',
            os.path.join('datasets', 'data', 'osf.json')
        )

    with open(fn) as src:
        osf_resources = _osfify_urls(json.load(src), return_restricted)

    try:
        resource = osf_resources[name]
    except KeyError:
        raise KeyError("Provided dataset '{}' is not valid. Must be one of: {}"
                       .format(name, sorted(osf_resources.keys()))) from None

    return resource


def get_data_dir(data_dir=None):
    """
    Get path to neuromaps data directory.

    Parameters
    ----------
    data_dir : str, optional
        Path to use as data directory. If not specified, will check for
        environmental variable 'NEUROMAPS_DATA'; if that is not set, will
        use `~/neuromaps-data` instead. Default: None

    Returns
    -------
    data_dir : str
        Path to use as data directory
    """
    if data_dir is None:
        data_dir = os.environ.get('NEUROMAPS_DATA',
                                  os.path.join('~', 'neuromaps-data'))
    data_dir = os.path.expanduser(data_dir)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    return data_dir


def _get_token(token=None):
    """
    Return `token` if provided or set as environmental variable.

    Parameters
    ----------
    token : str, optional
        OSF personal access token for accessing restricted annotations. Will
        also check the environmental variable 'NEUROMAPS_OSF_TOKEN' if not
        provided; if that is not set no token will be provided and restricted
        annotations will be inaccessible. Default: None

    Returns
    -------
    token : str
        OSF token
    """
    if token is None:
        token = os.environ.get('NEUROMAPS_OSF_TOKEN', None)

    return token


def _get_session(token=None):
    """
    Return requests.Session with `token` auth in header if supplied.

    Parameters
    ----------
    token : str, optional
        OSF personal access token for accessing restricted annotations. Will
        also check the environmental variable 'NEUROMAPS_OSF_TOKEN' if not
        provided; if that is not set no token will be provided and restricted
        annotations will be inaccessible. Default: None

    Returns
    -------
    session : requests.Session
        Session instance with authentication in header
    """
    session = requests.Session()
    token = _get_token(token)
    if token is not None:
        session.headers['Authorization'] = 'Bearer {}'.format(token)

    return session
