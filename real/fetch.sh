#!/bin/bash
# Download HydroRIVERS v1.0 for one region (eu, af, as, au, na, sa, ar, si) and extract only the .dbf table.
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p data
for r in "$@"; do
  curl -sSLo "data/HR_$r.zip" "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_${r}_shp.zip"
  python3 -c "import zipfile,sys; z=zipfile.ZipFile('data/HR_$r.zip'); [z.extract(i,'data') for i in z.infolist() if i.filename.endswith('.dbf')]"
done
