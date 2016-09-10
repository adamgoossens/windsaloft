import numpy as np
import netCDF4
import sys
import math
import argparse
import random
import struct
import threading

# convert a lat/long
def floorMod(a,n):
  return a - n * math.floor(a/n)

def ll2ij(lat, lon, latOrigin, longOrigin, dx, dy ):
  row = ( latOrigin - lat ) / dy
  col = floorMod( lon - longOrigin, 360 ) / dx
  return [int(round(row)),int(round(col))]

parser = argparse.ArgumentParser()

parser.add_argument("--minlong", help="Minimum (most western) longitude. Use negative numbers for western longitudes. ", type=float)
parser.add_argument("--maxlong", help="Maximum (most eastern) longitude. Use negative numbers for western longitudes.", type=float)
parser.add_argument("--minlat", help="Minimum (most southern) latitude. Use negative numbers for southern latitudes.", type=float)
parser.add_argument("--maxlat", help="Maximum (most northern) latitude. Use negative numbers for southern latitudes.", type=float)

parser.add_argument("level", help="The pressure level to interpolate for. In the same units as in your file (e.g. Pascals). Integer.", type=int)
parser.add_argument("input_file", help="Input file in NetCDF4 format. Gridded, lat/long with Z values as pressure surfaces")
parser.add_argument("output_file", help="Output file in binary. Each byte is a grid value")

args = parser.parse_args()

inputFile = args.input_file

f = netCDF4.Dataset( args.input_file )
desiredLevel = args.level
outputFile = args.output_file

levels = f.variables['level']

# the purpose of this is to extract the pressure level immediately
# above and immediately below our desired pressure
maxPressure = np.max(levels)
minPressure = np.min(levels)

stepSize = 2.5

# take args straight out of the NetCDF file if we didn't get them on the command
# line. These are *INCLUSIVE* values - i.e., we want to take from "minlong" to "maxlong" inclusive
minlong = min(f.variables['lon']) if args.minlong == None else args.minlong
minlat = min(f.variables['lat']) if args.minlat == None else args.minlat
maxlong = max(f.variables['lon']) if args.maxlong == None else args.maxlong
maxlat = max(f.variables['lat']) if args.maxlat == None else args.maxlat
totalCycles = f.variables['time'].size

#print(minlat, maxlat, " - ", minlong, maxlong)

if desiredLevel < minPressure or desiredLevel > maxPressure:
  print('Desired level is bounded by (' + repr(maxPressure) + ", " + repr(minPressure) + "). Check and try again.")
  sys.exit()

pLowerIdx = levels.size - np.searchsorted(levels[::-1],desiredLevel)
pUpperIdx = pLowerIdx - 1

# extract the lower and upper fields
# take all timesteps, all lat and longs, but a specific pressure
pressLower = levels[pLowerIdx]
pressUpper = levels[pUpperIdx]

#print(minlat,minlong)
#print(maxlat,maxlong)

# assumes scan mode 0 - latitudes grow DOWN from +90 degrees
# and longitudes grow EAST from 0 degrees
minRow, minCol = ll2ij( maxlat, minlong, max(f.variables['lat']), min(f.variables['lon']), 2.5, 2.5 )
maxRow, maxCol = ll2ij( minlat, maxlong, max(f.variables['lat']), min(f.variables['lon']), 2.5, 2.5 )

#print(minRow,maxRow,minCol,maxCol)

# add 1 because end indexes in Python slices aren't inclusive, and our maxRow/maxCol are zero-based numbers
fieldLower = f.variables['uwnd'][:,pLowerIdx,minRow:maxRow+1,minCol:maxCol+1]
fieldUpper = f.variables['uwnd'][:,pUpperIdx,minRow:maxRow+1,minCol:maxCol+1]

interp_u = fieldLower + math.log( pressLower / desiredLevel ) * (fieldUpper - fieldLower)/math.log( pressLower / pressUpper )

fieldLower = f.variables['vwnd'][:,pLowerIdx,minRow:maxRow+1,minCol:maxCol+1]
fieldUpper = f.variables['vwnd'][:,pUpperIdx,minRow:maxRow+1,minCol:maxCol+1]

interp_v = fieldLower + math.log( pressLower / desiredLevel ) * ( fieldUpper - fieldLower)/math.log( pressLower / pressUpper )

ncycles,nrow,ncol = interp_u.shape

print("Now calculating u and v components. Be patient - we need to go over {} records!".format(ncycles*nrow*ncol))

# the last dimension of 2 is to store windspeed and direction.
wnd = np.empty([ncycles, nrow, ncol, 2])

# hack alert: this really sucks - would very much like a better way of doing this...
# oh well, this will do for now.
for cycle in range(ncycles):
  for row in range(nrow):
    for col in range(ncol):
      u = interp_u[cycle,row,col]
      v = interp_v[cycle,row,col]
      spd = math.sqrt( u**2 + v**2 ) * 1.94384 # converts to knots (nm/hr)
      dirn = math.atan2(-u, -v) * 180 / math.pi
      dirn = dirn + 360 if dirn < 0 else dirn
      wnd[cycle,row,col,0] = spd
      wnd[cycle,row,col,1] = dirn

      if ( cycle % 100 == 0 and row == 0 and col == 0 and cycle != 0 ):
        print("Cycles {} to {} complete".format( cycle-100, cycle-1 ) )

print("Shape: " + repr(wnd.shape))
print("First element: [0,0,0] = [{},{}]".format(wnd[0,0,0,0],wnd[0,0,0,1]))
print("Last element: [{},{},{}] = [{},{}]".format(totalCycles-1, ( maxRow - minRow ), ( maxCol - minCol ), wnd[totalCycles-1,maxRow-minRow,maxCol-minCol,0],wnd[totalCycles-1,maxRow-minRow,maxCol-minCol,1]))

wnd = wnd * 100 # keep two decimal places
wnd = np.rint(wnd)

f = open(outputFile,'w')

# write some starting bytes to the file.
# (startLat, endLat, startLong, endLong) = 8 bytes total
f.write(struct.pack('h', totalCycles))
f.write(struct.pack('h', maxlat*10))
f.write(struct.pack('h', minlat*10))
f.write(struct.pack('h', minlong*10))
f.write(struct.pack('h', maxlong*10))
f.write(struct.pack('b', 25)) # 2.5 degree step, multiplied by 10.
f.write(wnd.astype('uint16').tostring())

f.close()
