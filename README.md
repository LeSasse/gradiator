# gradiator
Command line tool turn covariance matrices in tsv or csv files into gradients.


gradiator is heavily based on the fantastic brainspace toolbox, so make sure to
check out its [documentation](https://brainspace.readthedocs.io/en/latest/index.html)
and the [related paper](https://www.nature.com/articles/s42003-020-0794-7).

The idea of gradiator is to provide a quick and easy-to-use command line interface for the
computation of gradients using some symmetric covariance matrix in a csv or tsv file. gradiator
assumes that the first row of this matrix contains the column names, and like-wise it assumes
that the first column represents the index of the matrix.

The output gradients will be mapped to a NIfTI image in the same space as the volumetric atlas
you provide to gradiator.

# Set up

You may or may not want to set up a virtual environment.

```sh
python3 -m venv .examplevenv
source .examplevenv/bin/activate
pip install -U pip
```

You can simply install `gradiator` via PyPI:

```
pip install gradiator
```

Alternatively, you can install from GitHub.
Clone the repository to where you would like to install it and:
```
git clone https://github.com/LeSasse/gradiator.git
cd gradiator
pip install -e .
```

# How to use

Run `gradiator --help`:

```
usage: gradiator [-h] [--reference REFERENCE] [--n_components N_COMPONENTS]
               [--sparsity [SPARSITY ...]] [--kernel [KERNEL ...]]
               [--approach [APPROACH ...]] [--background BACKGROUND]
               matrix nii_atlas out_folder

Derive GradientMaps from symmetric ROIxROI covariance matrices saved in .tsv or
.csv files. For some arguments more than one values can be passed i.e. kernel. In
this case output will be generated for all possible combinations of parameters.

positional arguments:
  matrix                Path to the .csv or .tsv file containing the covariance
                        matrix. gradiator assumes that the first row is the column names,
                        and the first column is the index of the matrix.
  nii_atlas             Path to the nifti file that was used as a parcellation to
                        derive the ROI's of the covariance matrix and is used to
                        map gradients to nifti files.
  out_folder            Path to the directory in which output should be stored.

optional arguments:
  -h, --help            show this help message and exit
  --reference REFERENCE, -r REFERENCE
                        Path to a covariance matrix which should be used to create
                        reference gradients for alignment.
  --n_components N_COMPONENTS, -n N_COMPONENTS
                        Number of components to extract. (Int: default 5)
  --sparsity [SPARSITY ...], -s [SPARSITY ...]
                        One or more sparsity thresholds to be applied to covariance
                        matrix (float: default 0 and 0.9).
  --kernel [KERNEL ...], -k [KERNEL ...]
                        One or more kernels used to construct affinity matrix.
                        Available options are: pearson, spearman, normalized_angle,
                        cosine, gaussian or None.
  --approach [APPROACH ...], -a [APPROACH ...]
                        One or more approaches for the dimensionality reduction.
                        Available options are: pca, dm, le.
  --background BACKGROUND, -b BACKGROUND
                        Set the value of background voxels (i.e. voxels that are
                        labelled 0 in the Parcellation.). The absolute value of the
                        number handed over as 'background' will be subtracted from
                        the minimum gradient value to determine the value of
                        background voxels. If 'NaN' or 'nan' are provided, this
                        means that background values will be set to nan floating
                        points.In any case, 'NaN' values in the image are treated
                        exactly the same as background voxels.

```

# Example commands:

By default, gradiator will yield output for all possible combinations of gradient parameters:

```
gradiator my_covariance_matrix.tsv my_atlas.nii.gz path/to/my_desired_output_location
```

To specify only a few specific parameters, you could use the provided optional arguments as follows:

```sh
gradiator \
  my_covariance_matrix.tsv \
  my_atlas.nii.gz \
  path/to/my_desired_output_location \
  -n 5 \
  -s 0.9 \
  -a dm \ # diffusion map embedding
  -k normalized_angle
```

You can also set the value of the background voxels. For example by providing the strings
'nan' or 'NaN' with the `--background` option, the background will be set to 'NaN':

```
gradiator my_covariance_matrix.tsv my_atlas.nii.gz path/to/my_desired_output_location -b nan
```


However, typically it makes sense to set the background below the "cal_min" property of
the image header, which indicates the minimum display intensity of a NIfTI image.
From the [official NIfTI file specifications](https://nifti.nimh.nih.gov/pub/dist/src/niftilib/nifti1.h):

>  float cal_min;       /*!< Min display intensity */  /* float cal_min;       */

By handing over a numeric value to the `--background` option, the background will be set to 
`header['cal_min'] - abs(<your_provided_value>)`. This is useful, as the background can then
be easily distuingished from negative values on your gradient. the `cal_min` value of your resultant
gradient image is set to the lowest value on the gradient (which can often be negative).

So an example command for this can be:

```
gradiator my_covariance_matrix.tsv my_atlas.nii.gz path/to/my_desired_output_location -b 1000
```

Which will set the background voxels to the cal_min - 1000.

Now, it is also important to note, that any 'NaN' values in the gradient image are handled in the
same way as background voxels. That is, if a brain area has 'NaN' values in the covariance matrix,
then this area will be excluded from gradient computation, and the area will be 'NaN' in the image.
If you have other ideas on how 'NaN' values can be handled, feel free to make an issue.