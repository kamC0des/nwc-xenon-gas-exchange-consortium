"""Configuration file."""
import os
import sys

from ml_collections import config_dict

# parent directory
sys.path.append("..")

from config import base_config, config_utils
from utils import constants


class Config(base_config.Config):
    """Config file.

    Inherit from base_config.Config and override the parameters.
    """

    def __init__(self):
        """Initialize config parameters."""
        super().__init__()

        # directory containing subject data and subject ID for output
        self.data_dir = "uva/Xe129_0921"
        self.subject_id = "Xe129_0921"

        # what kind of segmentation to use (e.g., CNN_VENT, MANUAL_VENT)
        self.segmentation_key = constants.SegmentationKey.CNN_VENT.value
        #self.segmentation_key = constants.SegmentationKey.MANUAL_VENT.value
        #self.manual_seg_filepath = os.path.join(self.data_dir, "mask_reg_corrected.nii")

        # RBC to membrane ratio, e.g., from calibration
        self.rbc_m_ratio = 0.386

        self.multi_echo = False

        # set reference data distribution: manual or automatic
        self.reference_data_key = constants.ReferenceDataKey.DUKE_REFERENCE.value

        # override specific reconstruction parameters, as set in Recon class below
        self.recon = Recon()


class Recon(base_config.Recon):
    """Define reconstruction configurations.

    Attributes:
        scan_type: str, the scan type
        kernel_sharpness_lr: float, the kernel sharpness for low resolution, higher
            SNR images
        kernel_sharpness_hr: float, the kernel sharpness for high resolution, lower
            SNR images
        n_skip_start: int, the number of frames to skip at the beginning
        n_skip_end: int, the number of frames to skip at the end
        key_radius: int, the key radius for the keyhole image
    """

    def __init__(self):
        """Initialize the reconstruction parameters."""
        super().__init__()

        # default scan type, see config_utils.py
        self.scan_type = constants.ScanType.NORMALDIXON.value
        #self.n_skip_start = config_utils.get_n_skip_start(self.scan_type)
        self.n_skip_start = 0

        self.remove_noisy_projections = True

        self.del_x = -5
        self.del_y = -5
        self.del_z = -5

        self.recon_proton = False


def get_config() -> config_dict.ConfigDict:
    """Return the config dict. This is a required function.

    Returns:
        a ml_collections.config_dict.ConfigDict
    """
    return Config()
