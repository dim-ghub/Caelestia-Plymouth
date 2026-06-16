# Caelestia Plymouth Boot Animation

A premium, high-resolution Plymouth boot splash theme inspired by the Google Pixel boot animation, customized with the Caelestia crescent and stars logo.

## Features

- **4x Super-Sampled Anti-Aliasing**: All animation transforms (scaling, rotations, blurs) are computed natively at a massive **2048x2048** resolution, then downsampled to **512x512** using high-quality LANCZOS interpolation. This delivers perfectly smooth vector curves without any pixelation or jaggies.
- **Material Design "Sunny" Sun Shape**: A soft, flower-like 8-pointed star in vibrant Material yellow (`#ffd54f`) that slowly rotates at the center of the orbit paths.
- **Planetary Keplerian Intro**: Four colored planets sequentially fade in and revolve around the sun at relative Keplerian speeds before spiraling in and merging.
- **SDDM Locklike Morph**: The merged core expands and spins out to form the Caelestia logo, replicating the premium 720° overshoot rotation and scale bounce from the SDDM theme.
- **Material 3 Expressive Loading Circle**: A squiggly Material Design 3 loading shape (`SoftBurst` -> `Sunny` -> `Pill`) morphs dynamically on underdamped spring physics at the bottom.
- **Pitch Black Background**: Set to `#000000` for deep contrast.

---

## File Structure

- `caelestia-plymouth.plymouth` - Theme descriptor file.
- `caelestia-plymouth.script` - Theme animation, alignment, and display script.
- `generate_frames.py` - Python script that dynamically generates the 360 high-resolution transparent PNG frames from the SVG logo.
- `image.svg` - Original vector source asset containing the Caelestia logo and stars.
- `PKGBUILD` - Arch Linux packaging recipe that automates frame compilation and installation.
- `README.md` - Project documentation.

---

## Installation & Deployment

### 1. On Arch Linux (Recommended)

This project is fully packaged for Arch Linux. You can build and install it using standard Arch tools:

1. **Build the package**:
   In the root of the project repository, run:
   ```bash
   makepkg -s
   ```
   This will install all necessary build dependencies (like `librsvg` and `python-pillow`), run `generate_frames.py` to build the animation frames, and output the package archive `plymouth-theme-caelestia-1.1.1-1-any.pkg.tar.zst`.

2. **Install the package**:
   Install the generated package file using `pacman`:
   ```bash
   sudo pacman -U plymouth-theme-caelestia-1.1.1-1-any.pkg.tar.zst
   ```

3. **Set the theme**:
   Activate the theme and rebuild your initramfs:
   ```bash
   sudo plymouth-set-default-theme -R caelestia-plymouth
   ```

### 2. On Other Linux Distributions (Manual Copy)

If you are not using Arch Linux, you can generate the frames and copy them manually:

1. **Install python dependencies**:
   Ensure you have Python 3, Pillow (`python3-pillow`), and librsvg (`rsvg-convert` command) installed.

2. **Generate the frames**:
   Run the python script:
   ```bash
   ./generate_frames.py
   ```
   This will create a `caelestia-plymouth` directory containing all 360 frame PNGs.

3. **Copy theme folder**:
   Copy the `caelestia-plymouth` directory and the configuration files to your system Plymouth theme directory:
   ```bash
   sudo mkdir -p /usr/share/plymouth/themes/caelestia-plymouth
   sudo cp caelestia-plymouth.plymouth caelestia-plymouth.script /usr/share/plymouth/themes/caelestia-plymouth/
   sudo cp -r caelestia-plymouth/frame_*.png /usr/share/plymouth/themes/caelestia-plymouth/
   ```

4. **Select and rebuild**:
   Activate the theme (distribution specific commands may vary):
   ```bash
   sudo plymouth-set-default-theme -R caelestia-plymouth
   ```
