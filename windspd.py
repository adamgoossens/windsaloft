import sys
import math
import struct
from datetime import datetime

def floorMod(a,n):
  """
  Designed to handle negative numbers as appropriate. Will wrap a negative
  longitude around to an equivalent positive number that we can convert into
  a column value.
  """
  return a - n * math.floor(a/n)

def ll2ij(lat, lon, latOrigin, longOrigin, dLong, dLat ):
  """
  Given a latitude, longitude, origins and lat/long steps, determine the 
  row,col (i,j) offsets into our data grid.
  """
  row = ( latOrigin - lat ) / dLat
  col = floorMod( lon - longOrigin, 360 ) / dLong
  return [int(round(row)),int(round(col))]

def input_num( prompt, min_num, max_num, inclusive = False ):
  """
  Ask for a number and ensure it's between the appropriate bounds, inclusive if
  required.
  """
  while True:
    try:
      temp = raw_input( prompt )
      num = float(temp)

      if ( inclusive and ( num < min_num or num > max_num ) ) or ( not inclusive and ( num <= min_num or num >= max_num ) ):
        print("Number needs to be between {} and {}, {}.".format(min_num,max_num, "inclusive" if inclusive else "exclusive"))
        continue
      
      return num
    
    except ( ValueError, SyntaxError ):
      print("Number needs to be between {} and {}, {}. Press Ctrl+C if you want to quit.".format(min_num,max_num, "inclusive" if inclusive else "exclusive"))
    
file = sys.argv[1]
f = open(file,'rb')
dumpf = open('dumpfile.txt','w')

# read the file header - values in the file header need to be divided by 10
# to restore the single decimal place (except for the cycle count)
totalCycles = struct.unpack('h', bytearray(f.read(2)))[0]
latStart = struct.unpack('h', bytearray(f.read(2)))[0] / 10.0
latEnd = struct.unpack('h', bytearray(f.read(2)))[0] / 10.0
lonStart = struct.unpack('h', bytearray(f.read(2)))[0] / 10.0
lonEnd = struct.unpack('h', bytearray(f.read(2)))[0] / 10.0
stepSize = struct.unpack('B', bytearray(f.read(1)))[0] / 10.0

dumpf.write("0-1 = " + repr(totalCycles) +"\n")
dumpf.write("2-3 = " + repr(latStart) +"\n")
dumpf.write("4-5 = " + repr(latEnd) +"\n")
dumpf.write("6-7 = " + repr(lonStart) +"\n")
dumpf.write("8-9 = " + repr(lonEnd ) +"\n")
dumpf.write("10 = " + repr(stepSize) +"\n")

FILE_DATA_START = 11 # skip over the file header

num_cycles = 1460
num_row = ( abs( latEnd - latStart ) / stepSize ) + 1
num_col = ( abs( lonEnd - lonStart ) / stepSize ) + 1
num_components = 2
data_size = 2

print("File looks good! Covers lat range [{}, {}] and long range [{}, {}]. Step size {} degrees. {} rows and {} cols. Cycle range [1,{}].".format(latStart, latEnd, lonStart, lonEnd, stepSize, num_row, num_col, totalCycles))

byte_offset = 11
#try:
  #spd = struct.unpack('h',bytearray(f.read(2)))[0]
  #dirn = struct.unpack('h',bytearray(f.read(2)))[0]
  
  #while byte_offset < 101:
    #dumpf.write(str(byte_offset) + "-" + str(byte_offset+1) + " = spd = " + str(spd)+"\n")
    
    #byte_offset = byte_offset + 2
    #dumpf.write(str(byte_offset) + "-" + str(byte_offset+1) + " = dirn = " + str(dirn)+"\n")
    
    #byte_offset = byte_offset + 2
    
    #spd = struct.unpack('h',bytearray(f.read(2)))[0]
    #dirn = struct.unpack('h',bytearray(f.read(2)))[0]

#finally:
  #dumpf.close()
  
#f.close()

try:
  
  while True:
    
    try:
      date_str = str(raw_input('Enter a date string (MM/DD/YYYY). Leave blank for today: '))
      if date_str == '':
        dt = datetime.today()
      else:
        dt = datetime.strptime(date_str, '%m/%d/%Y')
    except ValueError:
      print('Bad date. Try again')
      continue
    
    day_of_year = dt.timetuple().tm_yday
    print('OK! Date = ' + dt.strftime('%m/%d/%Y') + ', Day of year = ' + str(day_of_year))
    cycle = input_num( 'Cycle within day? ( 1 = 00Z, 2 = 06Z, 3 = 12Z, 4 = 18Z): ', 1, 4, True )
    lat = input_num('What latitude?: ', min([latStart,latEnd]), max([latStart,latEnd]), True )
    lon = input_num( 'What longitude?: ', -180, 360, False )
    
    row,col = ll2ij(lat, lon, latStart, lonStart, stepSize, stepSize)

    cycle_offset = ( ( day_of_year - 1 ) * 4 ) + ( cycle - 1 )

    print row,col
    spd_offset = FILE_DATA_START + ( ( ( cycle_offset * num_row + row ) * num_col + col ) * num_components + 0 ) * data_size
    dirn_offset = FILE_DATA_START + ( ( ( cycle_offset * num_row + row ) * num_col + col ) * num_components + 1 ) * data_size
    print('Spd Offset: ' + repr(spd_offset))
    print('Dirn Offset: ' + repr(dirn_offset)) 
    f.seek(spd_offset)
    spd = struct.unpack('H',bytearray(f.read(2)))[0]
    spd = spd / 100.0

    f.seek(dirn_offset)
    dirn = struct.unpack('H',bytearray(f.read(2)))[0]
    dirn = dirn  / 100.0
  
    # expand u and v
    #spd = round( math.sqrt( pow(u,2) + pow(v,2)) )
    #dirn = round( 180 / math.pi * math.atan2(u,v) )
    
    print("[" + repr(cycle_offset) + ", " + repr(row) + ", " + repr(col) + "] = " + repr(spd) + "kts @ " + repr(dirn) + "deg" )

except( KeyboardInterrupt ):
  f.close()
  print("\nBye!")
  
