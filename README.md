# Caelestia Plymouth Boot Animation

A premium, high-resolution Plymouth boot splash theme featuring a physically accurate inner solar system and custom Caelestia logo morph.

![Boot Splash Animation Preview](preview_solar.gif)

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

1. **Download or build the package**:
   - **Prebuilt Package (Recommended)**: Download the latest `plymouth-theme-caelestia-*-any.pkg.tar.zst` from the [Releases](https://github.com/dim/caelestia-plymouth/releases) page.
   - **From Source**: Alternatively, clone this repository and run `makepkg -s` in the root folder to compile the animation frames and generate the package.

2. **Install the package**:
   Install the package archive using `pacman`:
   ```bash
   sudo pacman -U plymouth-theme-caelestia-*-any.pkg.tar.zst
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
