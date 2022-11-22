# gradify
Command line tool turn covariance matrices in tsv or csv files into gradients.

# Set up

You may or may not want to set up a virtual environment.

```sh
python3 -m venv .examplevenv
source .examplevenv/bin/activate
pip install -U pip
```
Then clone the repository to where you would like to install it.
```
git clone https://github.com/LeSasse/gradify.git
cd gradify
pip install -e .
```

# How to use

Run `gradify --help`:

```
usage: gradify [-h] [--n_components [N_COMPONENTS ...]] [--sparsity [SPARSITY ...]]
               [--kernel [KERNEL ...]] [--approach [APPROACH ...]]
               matrix nii_atlas out_folder

Derive GradientMaps from symmetric ROIxROI covariance matrices saved in .tsv or .csv
files. For some arguments more than one values can be passed i.e. kernel. In this case
output will be generated for all possible combinations of parameters.

positional arguments:
  matrix                Path to the .csv or .tsv file containing the covariance matrix.
  nii_atlas             Path to the nifti file that was used as a parcellation to
                        derive the ROI's of the covariance matrix and is used to
                        mapgradients to nifti files.
  out_folder            Path to the directory in which output should be stored.

optional arguments:
  -h, --help            show this help message and exit
  --n_components [N_COMPONENTS ...], -n [N_COMPONENTS ...]
                        Number of components to extract. (Int: default 5)
  --sparsity [SPARSITY ...], -s [SPARSITY ...]
                        One or more sparsity thresholds to be applied to covariance
                        matrix (float: default 0 and 0.9).
  --kernel [KERNEL ...], -k [KERNEL ...]
                        One or more kernels used to construct affinity matrix. Available
                        options are: pearson, spearman, normalized_angle, cosine,
                        gaussian or None.
  --approach [APPROACH ...], -a [APPROACH ...]
                        One or more approaches for the dimensionality reduction. Available
                        options are: pca, dm, le.

```
