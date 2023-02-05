"""Provide utility functions for the main tool."""

import os
from warnings import warn

import numpy as np
import pandas as pd
from nilearn import image


def load_matrix(path):
    """Load either csv or tsv files. delimiter is inferred from extension.

    Parameters
    ----------
    path : str or os.Path-like
        path to csv or tsv file containing the rows and columns of symmetric
        matrix

    Returns
    -------
    matrix : pd.DataFrame

    """
    _, ext = os.path.splitext(path)
    extensions = {".csv": ",", ".tsv": "\t"}

    return pd.read_csv(path, index_col=0, sep=extensions[ext])


def load_atlas(path):
    """Load atlas."""
    return image.load_img(path)


def check_symmetric(a, tol=1e-5):
    """Check symmetry by comparing matrix to its transpose."""
    if not np.all(np.abs(a - a.T) < tol):
        warn(
            f"Matrix may not be symmetric. Max value for 'matrix - matrix.T'"
            f" is {np.max(np.abs(a - a.T))}"
        )


def map_to_atlas(marker, atlas, bg_subtrahend):
    """Map values of a marker to the correct volumetric location in atlas.

    Parameters
    ----------
    marker : np.array, array-like
        length should correspond to number of regions in the given atlas
        index of each value corresponds to the label in the marker - 1,
        i.e. value at index 0 corresponds to ROI 1 etc.
    atlas : str, os.Path-like
        path to a nifti file for a volumetric parcellation

    Returns
    -------
    marker_img : niimg
        a nifti image of the marker values mapped back to the corresponding
        ROI's in the brain

    """
    marker = np.array(marker)
    atlas_array = np.array(atlas.dataobj)
    rois = np.unique(atlas_array)
    assert len(rois) - 1 == len(
        marker
    ), "Length of marker array and n ROI's are inconsistent!"
    marker_img_array = np.zeros(atlas_array.shape)
    marker_no_na = marker[~np.isnan(marker)]
    marker_min = np.min(marker_no_na)
    marker_max = np.max(marker_no_na)

    for roi in rois:
        roi = int(roi)
        if roi == 0:
            continue

        value = marker[roi - 1]
        marker_img_array[atlas_array == roi] = value

    marker_img_array[atlas_array == 0] = marker_min - bg_subtrahend
    marker_img_array[np.isnan(marker_img_array)] = marker_min - bg_subtrahend

    grad_img = image.new_img_like(atlas, marker_img_array)
    grad_img.header["cal_max"] = marker_max
    grad_img.header["cal_min"] = marker_min
    return grad_img
