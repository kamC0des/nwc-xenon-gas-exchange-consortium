# Xenon Gas Exchange Pipeline

> **Note:** This repository was cloned from the [Duke Xenon Gas Exchange Consortium](https://github.com/TeamXenonDuke/xenon-gas-exchange-consortium) and has undergone significant modifications. Files with notable changes include:
> `reconstruction.py`, `plot.py`, `system_model.py`, `subject_classmap.py`, `assets/html/clinical.html`, `assets/html/qa.html`, and `assets/html/grayscale.html`.
> For any unexpected behavior in these files, compare against the corresponding file in the upstream Duke repository.

---

## Getting Started

### 1. Clone This Repository

```bash
git clone <this-repo-url>
```

### 2. Set Up Your Environment

Follow the environment setup instructions from the [Duke repository README](https://github.com/TeamXenonDuke/xenon-gas-exchange-consortium).

> ⚠️ Complete the steps **in the described order** and follow the instructions appropriate for your operating system (macOS, Windows via WSL, or Linux).

To streamline steps 2.2 and 2.3 of the installation process, run the provided setup script:

```bash
bash .setup.sh
```

If the script fails, manual installation instructions are available at the bottom of the Duke repository README.

### 3. Run the Pipeline

To run the reconstruction pipeline using one of UVA's lung scans:

```bash
python main.py --config ./config/tests/Xe129_0921_config.py
```

---

## Known Issues & Pitfalls

### ANTs / N4BiasFieldCorrection — Runtime Error (`GLIBCXX` / `CXXABI` mismatch)

A common failure occurs during the bias field correction step (`N4BiasFieldCorrection`), producing an error like:

```
libstdc++.so.6: version `GLIBCXX_3.4.32' not found
CXXABI_1.3.15 not found
```

This typically causes the pipeline to crash later with a `FileNotFoundError` for `biasfield.nii`, since the correction step never successfully completed.

#### Cause

This is **not** an issue with the Python code or reconstruction pipeline. It is caused by a mismatch between:

- the version of the C++ standard library (`libstdc++`) required by the compiled ANTs binary, and
- the version available on the system — common on WSL or older Linux distributions.

Even if ANTs compiles successfully, the binary may still link against an older system library at runtime.

#### Solution

Install a compatible C++ runtime in your conda environment and force the pipeline to use it:

```bash
conda install -c conda-forge libstdcxx-ng
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
```

To make this fix **persistent across sessions**:

```bash
mkdir -p $CONDA_PREFIX/etc/conda/activate.d
nano $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
```

Add the following line to that file:

```bash
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
```

Then reactivate your environment:

```bash
conda deactivate
conda activate XeGas
```

#### Recommended Alternative

Install ANTs directly via conda rather than compiling manually — this avoids most library compatibility issues:

```bash
conda install -c conda-forge ants
```
