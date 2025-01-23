#!/usr/bin/env python

import os
from subprocess import Popen, PIPE
import sys
from osgeo import osr, ogr, gdal
import zipfile
import numpy as np
import glob
import pandas as pd

def read_attribute(shapefile,row):
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(shapefile)
	layer = dataSource.GetLayer(0)
	attributelist = []
	for feature in layer:
		attribute = feature.GetField(row)
		attributelist.append(attribute)
	return attributelist

shapezipfile = sys.argv[1]
exposureval = 100

NIRfile = 'NIR_'+'_'.join(shapezipfile.split('_')[1:-1])+'.csv'
NIR_df = pd.read_csv(NIRfile, sep=";", dtype={"MACS": str, "date": str, "time": str, "lat": float, "lon": float, "alt": float, "yaw": float, "pitch": float, "roll": float, "WKT": str})
NIR_df['time'] = pd.to_datetime(NIR_df['time']).dt.time
NIR_df = NIR_df.sort_values(by='time').reset_index(drop=True)

TIRfile = 'TIR_'+'_'.join(shapezipfile.split('_')[1:-1])+'.csv'
TIR_df = pd.read_csv(TIRfile, sep=";", dtype={"MACS": str, "date": str, "time": str, "lat": float, "lon": float, "alt": float, "yaw": float, "pitch": float, "roll": float, "WKT": str})
TIR_df['time'] = pd.to_datetime(TIR_df['time']).dt.time
TIR_df = TIR_df.sort_values(by='time').reset_index(drop=True)

#unpacking the zipped shapefile
with zipfile.ZipFile(shapezipfile, 'r') as zip_ref:
	zip_ref.extractall()

macsRGBpath = read_attribute(shapezipfile[:-4]+'.shp',0)
macsRGBdate = read_attribute(shapezipfile[:-4]+'.shp',1)
macsRGBtime =  read_attribute(shapezipfile[:-4]+'.shp',2)
macsRGBpoly = read_attribute(shapezipfile[:-4]+'.shp',9)
macsRGBtime = pd.to_datetime(macsRGBtime, format='%H:%M:%S.%f').time
RGB_df = pd.DataFrame({'macsRGBpath':macsRGBpath,'macsRGBdate':macsRGBdate,'macsRGBtime':macsRGBtime,'macsRGBpoly':macsRGBpoly})
RGB_df = RGB_df.sort_values(by='macsRGBtime').reset_index(drop=True)

idx = NIR_df['time'].searchsorted(RGB_df['macsRGBtime'])
NIR_files = NIR_df['MACS'][idx]

idx = TIR_df['time'].searchsorted(RGB_df['macsRGBtime'])
TIR_files = TIR_df['MACS'][idx]

#removing the unzipped shapefile
shapetiles = np.array([shapezipfile[:-4]+'.cpg',shapezipfile[:-4]+'.dbf',shapezipfile[:-4]+'.qmd',shapezipfile[:-4]+'.prj',shapezipfile[:-4]+'.shp',shapezipfile[:-4]+'.shx'])
for i in np.arange(len(shapetiles)):
	os.remove(shapetiles[i])

selected_macsfiles = []
for index, row in RGB_df.iterrows():
	RGB_file = row.macsRGBpath.split('/')[-1]
	RGB_file_exposureval = RGB_file.split('_')[2].split('.')[0]
	if int(RGB_file_exposureval) == exposureval:
		selected_macsfiles = np.append(selected_macsfiles,row.macsRGBpath)
		selected_macsfiles = np.append(selected_macsfiles,NIR_files.iloc[index])
		selected_macsfiles = np.append(selected_macsfiles,TIR_files.iloc[index])
		selected_macsfiles = np.append(selected_macsfiles,row.macsRGBdate)
		selected_macsfiles = np.append(selected_macsfiles,row.macsRGBtime)
		selected_macsfiles = np.append(selected_macsfiles,row.macsRGBpoly)

selected_macsfiles = selected_macsfiles.reshape(int(len(selected_macsfiles)/6),6)
outname = '_'.join(shapezipfile.split('_')[1:-1])+'_selected.csv'
np.savetxt(outname,selected_macsfiles, fmt='%s', delimiter=';', newline='\n', header='RGB;NIR;TIR;date;time;WKT', footer='', comments='', encoding=None)
