#!/usr/bin/env bash
# Downloads the Google Fonts used by the video scripts into ./fonts (OFL / Apache licensed).
# Source: the google/fonts GitHub repository, served through the jsDelivr CDN.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fonts
BASE="https://cdn.jsdelivr.net/gh/google/fonts@main"
FONTS=(
  "ofl/baloo2/Baloo2[wght].ttf"
  "ofl/caveat/Caveat[wght].ttf"
  "ofl/cormorantgaramond/CormorantGaramond[wght].ttf"
  "ofl/dancingscript/DancingScript[wght].ttf"
  "ofl/greatvibes/GreatVibes-Regular.ttf"
  "ofl/montserrat/Montserrat[wght].ttf"
  "ofl/pacifico/Pacifico-Regular.ttf"
  "ofl/playfairdisplay/PlayfairDisplay-Italic[wght].ttf"
  "ofl/playfairdisplay/PlayfairDisplay[wght].ttf"
  "ofl/poppins/Poppins-Bold.ttf"
  "ofl/poppins/Poppins-Medium.ttf"
  "ofl/poppins/Poppins-SemiBold.ttf"
)
for f in "${FONTS[@]}"; do
  name="$(basename "$f")"
  if [ -s "fonts/$name" ]; then echo "have  $name"; continue; fi
  # square brackets must be percent-encoded in the URL
  url="$BASE/${f//\[/%5B}"; url="${url//\]/%5D}"
  echo "fetch $name"
  curl -fsSL "$url" -o "fonts/$name"
done
echo "done: $(ls fonts | wc -l) font files in $(pwd)/fonts"
