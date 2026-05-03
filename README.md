1. git clone this workspace
2. Instructions for preparing your coding environment for this workspace can be found and should be followed from the README from this github: https://github.com/TeamXenonDuke/xenon-gas-exchange-consortium
3. Instructions should be followed and verified in the described order and in accordance to the user's machine (Mac, Windows (WSL), Linux etc.)
4. Utilize .setup.sh to complete step 2.2 and 2.3 of the installation process but in the case that fails manual installation is covered at the bottom end of the README
5. Use this command: python main.py --config ./config/tests/Xe129_0921_config.py to run the pipeline's reconstruction with one of UVA's lung scans

6. Relevant pitfalls:
    ANTs / N4BiasFieldCorrection runtime error (GLIBCXX / CXXABI mismatch)
    A common failure occurs during the bias field correction step (N4BiasFieldCorrection) with an error similar to:
    
    libstdc++.so.6: version `GLIBCXX_3.4.32' not found
    CXXABI_1.3.15 not found
    
    This typically causes the pipeline to crash later with a FileNotFoundError for biasfield.nii, since the correction step never successfully ran.
    
    Cause:
    This is not an issue with the Python code or reconstruction pipeline. It is caused by a mismatch between:
    
    the version of the C++ standard library (libstdc++) required by the compiled ANTs binary, and
    the version available on the system (common on WSL or older Linux distributions).
    
    Even if ANTs is compiled successfully, the binary may still try to use an older system library at runtime.
    
    Solution:
    Install a compatible version of the C++ runtime in your conda environment and force the pipeline to use it:
    
    conda install -c conda-forge libstdcxx-ng
    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
    
    To make this fix persistent across sessions:
    
    mkdir -p $CONDA_PREFIX/etc/conda/activate.d
    nano $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
    
    Add the following line:
    
    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
    
    Then reactivate your environment:
    
    conda deactivate
    conda activate XeGas
    
    Alternative (recommended):
    Install ANTs directly via conda instead of compiling manually:
    
    conda install -c conda-forge ants
    
    This avoids most library compatibility issues.


P.S: This repository was cloned from the Duke repository and has gone through numerous edits and iterations noteably with changes in the reconstruction.py, plot.py, system_model.py, subject_classmap.py, assets/html/clinical.html, assests/html/qa.html and assests/html/grayscale.html. So any questions regarding unnormal behavior or implementation regarding any of these files should be resolved by comparing to the corresponding file in the Duke repository.
   




