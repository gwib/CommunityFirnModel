import os
import subprocess 
modelDiffs = ['artS', 'artT', 'cro']

for m in modelDiffs:

	os.system('gdalwarp -q -cutline /Users/GalinaJonat/Documents/FirnProject/dipmap/input/gadm36_GRL_shp/gadm36_GRL_0.shp -tr 0.02735 0.00847 -of GTiff /Users/GalinaJonat/Documents/FirnProject/dipmap/'+m+'Diff.asc /Users/GalinaJonat/Documents/FirnProject/dipmap/'+m+'Diff_clipped.tif')