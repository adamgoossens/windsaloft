#!/bin/bash
declare -A elevations
elevations[8000]=753
elevations[10000]=697
elevations[15000]=572
elevations[18000]=506
elevations[21000]=446
elevations[24000]=393
elevations[27000]=344
elevations[30000]=301
elevations[33000]=262
elevations[36000]=227
elevations[39000]=196
elevations[42000]=170

for i in "${!elevations[@]}"
do
  echo "Running: python interpolate.py --minlong=110 --maxlong=160 --minlat=-45 --maxlat=-9 ${elevations[$i]} wnd.4Xday.1981-2010.ltm.nc elev/north_america/$i"
  eval "python interpolate.py --minlong=110 --maxlong=160 --minlat=-45 --maxlat=-9 ${elevations[$i]} wnd.4Xday.1981-2010.ltm.nc elev/aus/$i &"
done
