'''
'''
"""Reconstruct 3D MRI image from k-space data using SigPy least-squares NUFFT."""
'''
import time
import numpy as np
import sigpy as sp
import sigpy.mri as mr
from absl import app, logging

from utils import img_utils, io_utils

def normalize_matrix(matrix, a=-0.5, b=0.5):
 
    """
 
    Normalize the values in the matrix to the range [a, b].
 
    Parameters:
 
    - matrix: 2D list or numpy array to normalize.
 
    - a: the minimum value of the target range.
 
    - b: the maximum value of the target range.
 
    Returns:
 
    - A numpy array with the values normalized to [a, b].
 
    """
 
    # Convert the matrix to a numpy array if it is not already one
 
    matrix = np.array(matrix)
 


 
    # Normalize the matrix
 
    normalized_matrix = (matrix - np.min(matrix)) / (np.max(matrix) - np.min(matrix))
 
    normalized_matrix = normalized_matrix * (b - a) + a
    return normalized_matrix


def reconstruct(
    data: np.ndarray,
    traj: np.ndarray,
    kernel_sharpness: float = 0.32,
    kernel_extent: float = 0.32 * 9,
    image_size: int = 128,
    overgrid_factor: int = 2,
    n_dcf_iter: int = 20,
    max_iter: int = 30,
    verbosity: bool = True,
) -> np.ndarray:
    """Reconstruct MRI image using iterative least-squares NUFFT.

    Args:
        data (np.ndarray): k-space data (K,1) or (K,)
        traj (np.ndarray): k-space trajectory (K,3)
        image_size (int): reconstructed image dimension
        overgrid_factor (int): NUFFT oversampling factor
        n_dcf_iter (int): Pipe density compensation iterations
        max_iter (int): least squares iterations
        verbosity (bool): logging output

    Returns:
        np.ndarray: reconstructed image volume
    """

    start_time = time.time()

    if verbosity:
        logging.info("Starting least-squares NUFFT reconstruction")
    print()
    print("traj min:", traj.min())
    print("traj max:", traj.max())
    print()
    # Remove singleton dimensions
    data = np.squeeze(data)

    

    img_shape = (image_size, image_size, image_size)

    # SigPy expects k-space coordinates in radians [-π, π]
    traj_scaled = traj * img_shape[0] * np.pi
    traj_scaled = image_size*normalize_matrix(traj_scaled)
    # ------------------------------------------------
    # Density Compensation (Pipe method)
    # ------------------------------------------------
    if verbosity:
        logging.info("Computing density compensation (Pipe method)")

    dcf = mr.dcf.pipe_menon_dcf(
        traj_scaled,
        img_shape,
        max_iter=n_dcf_iter
    )

    weighted_data = data * dcf

    # ------------------------------------------------
    # NUFFT Operator
    # ------------------------------------------------
    if verbosity:
        logging.info("Creating NUFFT operator")

    A = sp.linop.NUFFT(
        img_shape,
        traj_scaled,
        oversamp=overgrid_factor
    )

    # ------------------------------------------------
    # Adjoint NUFFT Initialization (good starting point)
    # ------------------------------------------------
    if verbosity:
        logging.info("Computing adjoint NUFFT initialization")

    x0 = sp.nufft_adjoint(
        weighted_data,
        traj_scaled,
        oshape=img_shape,
        oversamp=overgrid_factor
    )
    #image = x0.copy()
    # ------------------------------------------------
    # Least Squares Reconstruction
    # ------------------------------------------------
    
    if verbosity:
        logging.info("Running iterative least-squares reconstruction")

    image = sp.app.LinearLeastSquares(
        A,
        data,
        x=x0,
        max_iter=max_iter,
    ).run()

    image = np.flip(image, axis=(0, 1, 2))
    image = np.rot90(np.rot90(image, 1, axes=(1, 2)), 3, axes=(0, 2))  # Rearrange axes
    image = np.rot90(image, 1, axes=(1,0))  # Additional rotation

    end_time = time.time()
    logging.info("Execution time: %.2f seconds", end_time - start_time)
    
    #image = img_utils.flip_and_rotate_image(images=image,)
    return image

    #use the first output for the image do not iterate to preserve time and get a better output
def main(argv):
    """Demonstrate non-Cartesian MRI reconstruction using SigPy."""

    logging.info("Loading demo MRI data")

    data = io_utils.import_mat("assets/demo_radial_mri_data.mat")["data"]
    traj = io_utils.import_mat("assets/demo_radial_mri_traj.mat")["traj"]

    image = reconstruct(
        data=data,
        traj=traj,
        image_size=128,
        overgrid_factor=2,
        n_dcf_iter=20,
        max_iter=30,
        verbosity=True,
    )

    # Fix orientation

    
    image = img_utils.flip_and_rotate_image(image)
    

    # Export magnitude image
    io_utils.export_nii(np.abs(image), "tmp/demo_nufft_lsq.nii")

    logging.info("Reconstruction complete!")


if __name__ == "__main__":
    app.run(main)
'''
"""Reconstruct 3D image from k-space data and trajectory."""

import time

import numpy as np
from absl import app, logging

from recon import dcf, kernel, proximity, recon_model, system_model
from utils import img_utils, io_utils

import sigpy as sp


def reconstruct_lsq(
    data: np.ndarray,
    traj: np.ndarray,
    kernel_sharpness: float = 0.32,
    kernel_extent: float = 0.32 * 9,
    overgrid_factor: int = 3,
    image_size: int = 128,
    n_dcf_iter: int = 20,
    verbosity: bool = True,
) -> np.ndarray:
    print("This is the image shape passed in")
    print()
    print(image_size)
    """Reconstruct k-space data and trajectory.

    Args:
        data (np.ndarray): k space data of shape (K, 1)
        traj (np.Jlndarray): k space trajectory of shape (K, 3)
        kernel_sharpness (float): kernel sharpness. larger kernel sharpness is sharper
            image
        kernel_extent (float): kernel extent.
        overgrid_factor (int): overgridding factor
        image_size (int): target reconstructed image size
            (image_size, image_size, image_size)
        n_pipe_iter (int): number of dcf iterations
        verbosity (bool): Log output messages

    Returns:
        np.ndarray: reconstructed image volume
    """
    start_time = time.time()
    prox_obj = proximity.L2Proximity(
        kernel_obj=kernel.Gaussian(
            kernel_extent=kernel_extent,
            kernel_sigma=kernel_sharpness,
            verbosity=verbosity,
        ),
        verbosity=verbosity,
    )
    system_obj = system_model.MatrixSystemModel(
        proximity_obj=prox_obj,
        overgrid_factor=overgrid_factor,
        image_size=np.array([image_size, image_size, image_size]),
        traj=traj,
        verbosity=verbosity,
    )
    dcf_obj = dcf.IterativeDCF(
        system_obj=system_obj, dcf_iterations=n_dcf_iter, verbosity=verbosity
    )
    recon_obj = recon_model.LSQgridded(
        system_obj=system_obj, dcf_obj=dcf_obj, verbosity=verbosity
    )
    image = recon_obj.reconstruct(data=data, traj=traj)
    print("This is the image shape at the end")
    print()
    print(image.shape)
    del recon_obj, dcf_obj, system_obj, prox_obj
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info("Execution time: {:.2f} seconds".format(execution_time))
    return image

def reconstruct( #reconstruct_sigpy 
    data: np.ndarray,
    traj: np.ndarray,
    kernel_sharpness: float = 0.32,
    kernel_extent: float = 0.32 * 9,
    overgrid_factor: int = 3,
    image_size: int = 128,
    n_dcf_iter: int = 20,
    verbosity: bool = True,
) -> np.ndarray:
    """Reconstruct k-space data and trajectory.

    Args:
        data (np.ndarray): k space data of shape (K, 1)
        traj (np.Jlndarray): k space trajectory of shape (K, 3)
        kernel_sharpness (float): kernel sharpness. larger kernel sharpness is sharper
            image
        kernel_extent (float): kernel extent.
        overgrid_factor (int): overgridding factor
        image_size (int): target reconstructed image size
            (image_size, image_size, image_size)
        n_pipe_iter (int): number of dcf iterations
        verbosity (bool): Log output messages

    Returns:
        np.ndarray: reconstructed image volume
    """
    oshape=np.array([image_size, image_size, image_size])
    
    #traj = traj.reshape((traj.shape[0] * traj.shape[1], 3))
    
    start_time = time.time()
    prox_obj = proximity.L2Proximity(
        kernel_obj=kernel.Gaussian(
            kernel_extent=kernel_extent,
            kernel_sigma=kernel_sharpness,
            verbosity=verbosity,
        ),
        verbosity=verbosity,
    )
    system_obj = system_model.MatrixSystemModel(
        proximity_obj=prox_obj,
        overgrid_factor=overgrid_factor,
        image_size=np.array([image_size, image_size, image_size]),
        traj=traj,
        verbosity=verbosity,
    )
    dcf_obj = dcf.IterativeDCF(
        system_obj=system_obj, dcf_iterations=n_dcf_iter, verbosity=verbosity
    )

    dcf_obj.dcf = dcf_obj.dcf.reshape((data.shape[0], data.shape[1]))
    
    data_dcf = (data * dcf_obj.dcf**0.82).reshape((-1,))

    traj = image_size*normalize_matrix(traj)
    
    recon_obj = sp.linop.NUFFT(
                ishape=oshape,
                coord=traj,
                oversamp=3,
                width=kernel_extent,
                toeplitz=False  # Use True if planning iterative inversion
            ).H
    print("This is the shape of the data after applying DCF") 
    print(data_dcf.shape)
    print()
    image = recon_obj(data_dcf)
    # image = system_obj.crop(image)
    print()
    print("cropped image shape:", image.shape)
    print()
    image = np.flip(image, axis=(0, 1, 2))
    image = np.rot90(np.rot90(image, 1, axes=(1, 2)), 3, axes=(0, 2))  # Rearrange axes
    image = np.rot90(image, 1, axes=(1,0))  # Additional rotation
    
    del recon_obj, dcf_obj, system_obj, prox_obj
    
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info("The reconstruction Execution time: {:.2f} seconds".format(execution_time))
    return image

def normalize_matrix(matrix, a=-0.5, b=0.5):

    """

    Normalize the values in the matrix to the range [a, b].

    Parameters:

    - matrix: 2D list or numpy array to normalize.

    - a: the minimum value of the target range.

    - b: the maximum value of the target range.

    Returns:

    - A numpy array with the values normalized to [a, b].

    """

    # Convert the matrix to a numpy array if it is not already one

    matrix = np.array(matrix)

 
    

    # Normalize the matrix

    normalized_matrix = (matrix - np.min(matrix)) / (np.max(matrix) - np.min(matrix))

    normalized_matrix = normalized_matrix * (b - a) + a
 
    return normalized_matrix
 


def main(argv):
    """Demonstrate non-cartesian reconstruction.

    Uses demo data from the assets folder.
    """
    data = io_utils.import_mat("assets/demo_radial_mri_data.mat")["data"]
    traj = io_utils.import_mat("assets/demo_radial_mri_traj.mat")["traj"]
    image = reconstruct(
        data=data,
        traj=traj,
        kernel_sharpness=1.0 / 3,
        kernel_extent=2,
        n_dcf_iter=10,
        verbosity=True,
    )
    image = img_utils.flip_and_rotate_image(image)
    io_utils.export_nii(np.abs(image), "tmp/demo_nufft.nii")

    logging.info("done!")


if __name__ == "__main__":
    app.run(main)
