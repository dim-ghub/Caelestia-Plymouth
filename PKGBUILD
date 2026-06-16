# Maintainer: Dim <dim@example.com>
pkgname=plymouth-theme-caelestia
pkgver=1.0
pkgrel=1
pkgdesc="Google Pixel style boot splash using the Caelestia logo for Plymouth"
arch=('any')
url="https://github.com/dim/caelestia-plymouth"
license=('GPL3')
depends=('plymouth')
makedepends=('librsvg' 'python-pillow')
source=("caelestia-plymouth.plymouth"
        "caelestia-plymouth.script"
        "generate_frames.py"
        "image.svg")
sha256sums=('SKIP'
            'SKIP'
            'SKIP'
            'SKIP')

build() {
  cd "$srcdir"
  # Run generator to build the frame sequence
  python3 generate_frames.py
}

package() {
  cd "$srcdir"
  
  # Create theme directory
  install -d "${pkgdir}/usr/share/plymouth/themes/caelestia-plymouth"
  
  # Install theme descriptor and script
  install -m644 caelestia-plymouth.plymouth "${pkgdir}/usr/share/plymouth/themes/caelestia-plymouth/"
  install -m644 caelestia-plymouth.script "${pkgdir}/usr/share/plymouth/themes/caelestia-plymouth/"
  
  # Install generated frame PNGs
  install -m644 caelestia-plymouth/frame_*.png "${pkgdir}/usr/share/plymouth/themes/caelestia-plymouth/"
}
