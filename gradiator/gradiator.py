"""Provide gradient output for covariance matrices."""

# Author: Leonard Sasse <l.sasse@fz-juelich.de>

import argparse
import os
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from brainspace.gradient import GradientMaps

from gradiator import check_symmetric, load_atlas, load_matrix, map_to_atlas


def validate_args(args):
    """Validate arguments."""
    all_kernels = [
        "normalized_angle",
        "gaussian",
        "pearson",
        "spearman",
        "cosine",
        None,
    ]
    all_approaches = ["pca", "dm", "le"]

    if not os.path.isfile(args.matrix):
        raise FileNotFoundError(f"{args.matrix} not found!")

    if not os.path.isfile(args.nii_atlas):
        raise FileNotFoundError(f"{args.nii_atlas} not found!")

    if not os.path.isdir(args.out_folder):
        raise FileNotFoundError(f"{args.out_folder} not found!")

    if args.n_components is None:
        args.n_components = 5

    if args.sparsity is None:
        args.sparsity = [0, 0.9]

    if args.kernel is None:
        args.kernel = all_kernels
    else:
        args.kernel = [k if k != "None" else None for k in args.kernel]

    if args.approach is None:
        args.approach = all_approaches

    return args


def parse_args():
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Derive GradientMaps from symmetric ROIxROI covariance "
            "matrices saved in .tsv or .csv files. For some arguments "
            "more than one values can be passed i.e. kernel. In this case"
            " output will be generated for all possible combinations of "
            "parameters."
        )
    )
    parser.add_argument(
        "matrix",
        type=str,
        help=(
            "Path to the .csv or .tsv file containing the covariance matrix."
            "gradiator assumes that the first row is the column names, "
            "and the first column is the index of the matrix."
          )
    )
    parser.add_argument(
        "nii_atlas",
        type=str,
        help=(
            "Path to the nifti file that was used as a parcellation to "
            "derive the ROI's of the covariance matrix and is used to map "
            "gradients to nifti files."
        ),
    )
    parser.add_argument(
        "out_folder",
        type=str,
        help=("Path to the directory in which output should be stored."),
    )
    parser.add_argument(
        "--reference",
        "-r",
        type=str,
        help=(
            "Path to a covariance matrix which should be used to "
            "create reference gradients for alignment."
        ),
    )
    parser.add_argument(
        "--n_components",
        "-n",
        type=int,
        help=("Number of components to extract. (Int: default 5)"),
    )
    parser.add_argument(
        "--sparsity",
        "-s",
        nargs="*",
        type=float,
        help=(
            "One or more sparsity thresholds "
            "to be applied to covariance matrix (float: default 0 and 0.9)."
        ),
    )
    parser.add_argument(
        "--kernel",
        "-k",
        nargs="*",
        help=(
            "One or more kernels used to construct affinity matrix."
            " Available options are: pearson, spearman, "
            "normalized_angle, cosine, gaussian or None."
        ),
    )
    parser.add_argument(
        "--approach",
        "-a",
        nargs="*",
        help=(
            "One or more approaches for the dimensionality reduction."
            " Available options are: pca, dm, le."
        ),
    )
    parser.add_argument(
        "--background",
        "-b",
        type=float,
        help=(
            "Set the value of background voxels (i.e. voxels that are "
            "labelled 0 in the Parcellation.). The absolute value of "
            "the number handed over as 'background' will be subtracted "
            "from the minimum gradient value to determine the value of back"
            "ground voxels. If 'NaN' or 'nan' are provided, this means that "
            "background values will be set to nan floating points."
            "In any case, 'NaN' values in the image are treated exactly the"
            " same as background voxels."
        ),
        default=100,
    )

    return parser.parse_args()


def main():
    """Perform main analysis.

    Take a symmetric matrix (ROI x ROI), perform dimensionality reductions
    obtaining n components, map each component back to the brain and save it as
    a nifti file. It is assumed that the csv or tsv's first column consists of
    the index, and the first row consists of the header row of the data frame.

    Further it is assumed that matrix rows and columns are both in order of
    labels in the parcellation file, i.e. row 0 corresponds to ROI 1 in the
    parcellation etc.
    """
    args = validate_args(parse_args())
    _, tail = os.path.split(args.matrix)
    matrix_name, _ = os.path.splitext(tail)

    out_folder = Path(args.out_folder)
    assert os.path.isdir(out_folder), f"{out_folder} is not a directory!"
    out_folder = out_folder / f"{matrix_name}_gradients"
    os.mkdir(out_folder)

    print(f"'{matrix_name}_gradients' folder created... ")
    print("Starting to construct GradientMaps ... ")

    atlas = load_atlas(args.nii_atlas)
    roixroi = load_matrix(args.matrix)
    nans = roixroi.isna().all(axis=0)
    no_nans = roixroi.loc[~nans.values, ~nans.values].values
    len_grads, _ = roixroi.shape

    check_symmetric(no_nans)

    n_total_grads = (
        len(args.sparsity)
        * len(args.approach)
        * len(args.kernel)
        * args.n_components
    )
    i_grad = 0

    alignment = None
    if args.reference is not None:
        reference = (
            load_matrix(args.reference).loc[~nans.values, ~nans.values].values
        )
        alignment = "procrustes"
        n_total_grads *= 2

    gradient_matrix = np.zeros((len_grads, n_total_grads))
    column_names = []
    for kernel, approach, sparsity in product(
        args.kernel, args.approach, args.sparsity
    ):

        gm = GradientMaps(
            n_components=args.n_components,
            approach=approach,
            kernel=kernel,
            alignment=alignment,
        )

        out_folder_setting = (
            out_folder / f"approach-{approach}" / f"kernel-{kernel}"
        )
        os.makedirs(out_folder_setting, exist_ok=True)

        if args.reference is None:
            gm.fit(no_nans, sparsity=sparsity)
            gradients_list = [gm.gradients_.T]
        else:
            gm.fit([no_nans, reference], sparsity=sparsity)
            gradients_list = [g.T for g in gm.aligned_]

        insert_idx = [x for x, y in enumerate(nans) if y]

        suffixes = ["gradient", "alignmentreference"]
        for gradients, suffix in zip(gradients_list, suffixes):
            for comp, grad in enumerate(gradients):
                i_grad += 1
                gradient_name = (
                    f"spars-{sparsity}_appr-{approach}_"
                    f"kernel-{kernel}_comp-{comp+1}_{suffix}"
                )

                print(f"GradientMap {i_grad}/{n_total_grads}", end="\r")
                column_names.append(gradient_name)

                new_grad = np.zeros(nans.values.shape)
                new_grad[insert_idx] = np.nan
                new_grad[new_grad == 0] = grad
                mapped = map_to_atlas(
                    new_grad, atlas, bg_subtrahend=abs(args.background)
                )
                mapped.to_filename(
                    out_folder_setting / f"{gradient_name}.nii.gz"
                )
                gradient_matrix[:, i_grad - 1] = new_grad

    pd.DataFrame(gradient_matrix, columns=column_names).to_csv(
        out_folder / f"{matrix_name}_gradients.tsv", sep="\t"
    )
