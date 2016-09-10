# Historical Winds Aloft

To build this dataset, you need to first download the uwnd and vwnd 4X daily long term average
datasets from the following URL:

ftp://ftp.cdc.noaa.gov/Datasets/ncep.reanalysis.derived/pressure/uwnd.4Xday.1981-2010.ltm.nc
ftp://ftp.cdc.noaa.gov/Datasets/ncep.reanalysis.derived/pressure/vwnd.4Xday.1981-2010.ltm.nc

You then need to concatenate these two files together using the ncks tools (NetCDF operators):

cp vwnd.4Xday.1981-2010.ltm.nc vwnd
ncks -A uwnd.4Xday.1981-2010.ltm.nc vwnd
mv vwnd wnd.4Xday.1981-2010.ltm.nc

interpolate.py will use the pressure surfaces within the wnd file to calculate any desired
pressure level you want. In an ISA standard atmosphere:

Feet     Millibar
8000   =   753
10000  =   697
15000  =   572
18000  =   506
21000  =   446
24000  =   393
27000  =   344
30000  =   301
33000  =   262
36000  =   227
39000  =   196
42000  =   170

Pick the millibar value according to the pressure altitude in feet you want. Say, 10000ft:

interpolate.py 697 wnd.4Xday.1981-2010.ltm.nc 10000.bin

That will interpolate the source data to create the outputs for 10000ft, dumping it in the 10000.bin file.

To query it, use windspd.py:

python windspd.py 10000
