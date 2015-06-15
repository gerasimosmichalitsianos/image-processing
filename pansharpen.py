
#!/usr/bin/env python

import os
import sys
import gc 
import numpy as np
from osgeo import osr, gdal

gdalRetileLocation = '/opt/PGSC/gdal/bin/gdal_retile.py'
gdalMergeLocation = '/opt/PGSC/gdal/bin/gdal_merge.py'
pythonLocation = '/opt/PGSC/anaconda/bin/python '

def writeImg(imgs, outname, dspan):

   '''
   function writeImg(imgs,outname,dspan): 
   This function writes out a 4-band Geotiff image. 
   The 4 Numpy arrays should be stored in the list 
   'imgs', an outname string should be provided, and
   the GDAL object dspan = gdal.Open(panfname.tif) 
   should also be provided, to extract map information. 

   ''' 

   if os.path.exists(outname):
      os.remove(outname)
   else: 
      nrows,ncols= imgs[0].shape 
      driv = gdal.GetDriverByName('GTiff')
      dst = driv.Create(outname, ncols, nrows, 4, gdal.GDT_Float32)
      dst.SetGeoTransform(dspan.GetGeoTransform())
      dst.SetProjection(dspan.GetProjection())
      dst.GetRasterBand(1).WriteArray(imgs[2])
      dst.GetRasterBand(2).WriteArray(imgs[1])
      dst.GetRasterBand(3).WriteArray(imgs[0])
      dst.GetRasterBand(4).WriteArray(imgs[3])
      dst=None
      del dst 

def getmultifname(panfname, content): 

    panbasename = os.path.basename(panfname).split('.')[0].split('________')[0]
    for name in content: 
        
        if ('M1BS' in name) and name.endswith('.tif') and ('_TOA-Multispec_Resampled.tif' in name): 
            basenamemulti = name.split('.')[0].split('_________')[0]
            if basenamemulti.replace('M1BS','P1BS') == panbasename: return name 
    return None 

def broveySharpen(dsmulti, dspan):

   '''
   function broveySharpen(dsmulti,dspan): 
   This function returns a list holding 4 pan-sharpened 
   images (Numpy arrays): the red, green, blue, and NIR 
   bands. The Brovey pan-sharpening technique is used here
   to pansharpen the Numpy arrays. The gdal objects 
   (dsmulti=gdal.Open(multifname.tif, dspan = gdal.Open(panfname.tif)
   should both be provided, so the arrays can be extracted. 
   ''' 

   try:

      with warn.catch_warnings():
         warn.filterwarnings('ignore',category=RuntimeWarning)

         pan   = dspan.GetRasterBand(1).ReadAsArray().astype(float)
         red   = dsmulti.GetRasterBand(3).ReadAsArray() 
         green = dsmulti.GetRasterBand(2).ReadAsArray()
         blue  = dsmulti.GetRasterBand(1).ReadAsArray()
         nir   = dsmulti.GetRasterBand(4).ReadAsArray()

         redsharp   = np.multiply( np.true_divide(red , red + green + blue + nir), pan)
         greensharp = np.multiply( np.true_divide(green , red + green + blue + nir), pan)
         bluesharp  = np.multiply( np.true_divide(blue , red + green + blue + nir), pan)
         nirsharp   = np.multiply( np.true_divide(nir , red + green + blue + nir), pan)

         return [redsharp,greensharp,bluesharp,nirsharp]
   except:
      return [None,None,None,None]
   

def fihsSharpen(dsmulti, dspan):

   '''
   function fihsSharpen(dsmulti,dspan): 
   This function returns a list holding 4 pan-sharpened 
   images (Numpy arrays): the red, green, blue, and NIR 
   bands. The FIHS pan-sharpening technique is used here
   to pansharpen the Numpy arrays. The gdal objects 
   (dsmulti=gdal.Open(multifname.tif, dspan = gdal.Open(panfname.tif)
   should both be provided, so the arrays can be extracted. 
   ''' 

   try:

      with warn.catch_warnings():
         warn.filterwarnings('ignore',category=RuntimeWarning)

         pan   = dspan.GetRasterBand(1).ReadAsArray().astype(float)
         red   = dsmulti.GetRasterBand(3).ReadAsArray() 
         green = dsmulti.GetRasterBand(2).ReadAsArray()
         blue  = dsmulti.GetRasterBand(1).ReadAsArray()
         nir   = dsmulti.GetRasterBand(4).ReadAsArray()

         L = (red+green+blue+nir)/float(4)
         redsharp   = red   + (pan - L) 
         greensharp = green + (pan - L)
         bluesharp  = blue  + (pan - L)
         nirsharp   = nir   + (pan - L) 

         return [redsharp,greensharp,bluesharp,nirsharp]
   except:
      return [None,None,None,None]

def main():

   '''
   function main(): 
   This function main() is called when this script is run. 
   This script should be run with one command line argument: 
   the string geotiff name of a 1-band panchromatic Geotiff 
   image file. The corresponding bicubic-resampled 
   multispectral image Geotiff file should also be in the 
   same directory. When this script is run, it produces 
   pan-sharpened multispectral Geotiff files (2 of them), using
   both the Brovey and fast intensity-hue-saturation (FIHS) 
   methods. This script actually breaks down the 
   panchromatic file and multispectral file into small tiles first
   (for the sake of not producing a MemoryError in Python). 
   From these, pan-sharpend Brovey/FIHS geotiff image files 
   are produced, and in the end, they are all put together 
   in 2 large single mosaic 4-band, pan-sharpened Geotiff 
   image files, one for Brovey, one for FIHS methods). 
   
   usage: 
   $ python pansharpen.py panfname.tif 

   '''

   usgMsg = '$ python pansharpen.py panfname.tif ' 
   try:
      panfname = sys.argv[1]
   except:
      print usgMsg
      sys.exit() 

   os.system('source /opt/PGSC/init-asp.sh')
   directory = os.path.dirname(panfname) 
   allfiles = os.listdir(directory)
   multifname = os.path.join(directory, getmultifname(panfname, allfiles))

   if os.path.isfile(panfname) and os.path.isfile(multifname): 

      dspan = gdal.Open(panfname)
      dsmulti = gdal.Open(multifname)

      if ('None' not in str(type(dspan))) and ('None' not in str(type(dsmulti))):

         fulloutnamefihs   = multifname.replace('_TOA-Multispec_Resampled.tif', '_TOA-Multispec_PanSharpenedFIHS.tif')
         fulloutnamebrovey = multifname.replace('_TOA-Multispec_Resampled.tif', '_TOA-Multispec_PanSharpenedBrovey.tif')
         
         if not os.path.exists(fulloutnamefihs) and not os.path.exists(fulloutnamebrovey):

            try: 

               # ---- tile up huge, resampled multispectral file
               dim=4.0
               nrows,ncols = dsmulti.RasterYSize, dsmulti.RasterXSize
               xtiledim,ytiledim = int(ncols/dim), int(nrows/dim)

               # ---- .csv files will go to same directory as pan/MS
               tileslistName    = multifname.replace('_TOA-Multispec_Resampled.tif','_TOA-Multispec_ResampledTiles.csv')
               tileslistNamePan = panfname.replace('_TOA-Pan.tif', '_TOA-PanTiles.csv')
               
               # ---- create a tile command and then subsequently run it, tiles go to directory as pan/MS 
               targetDirectory = os.path.dirname(panfname)
               tilecmd = pythonLocation + gdalRetileLocation + ' -ps ' + str(xtiledim) + ' ' + \
                         str(ytiledim) + ' -targetDir ' + targetDirectory + ' -csv ' + os.path.basename(tileslistName) + ' ' + multifname
               tilecmdPan = pythonLocation + gdalRetileLocation + ' -ps ' + str(xtiledim) + ' ' + \
                         str(ytiledim) + ' -targetDir ' + targetDirectory + ' -csv ' + os.path.basename(tileslistNamePan) + ' ' + panfname 

               os.system(tilecmd)
               os.system(tilecmdPan)

               if os.path.exists(tileslistName) and os.path.exists(tileslistNamePan): 
                  lines = open(tileslistName,'r').readlines()
                  linesPan = open(tileslistNamePan,'r').readlines()
               else:
                  print '.csv files do not exist: '
                  print tileslistName
                  print tileslistNamePan
                  sys.exit() 

               if len(lines)>0 and len(linesPan)>0 and (len(lines)==len(linesPan)): 

                  # ---- these lists will hold names of pan-sharpened tiles 
                  outputTileNamesBrovey,outputTileNamesFIHS = [], []

                  for i in range(len(lines)): 

                     # ---- get name of 4-band bicubic-resampled tile (geotiff), name of pan geotiff tile 
                     tilenametiff    = os.path.join(os.path.dirname(multifname), lines[i].split(';')[0])
                     tilenametiffPan = os.path.join(os.path.dirname(panfname), linesPan[i].split(';')[0])

                     # ---- make sure our file files (both pan+multi) exist 
                     if not os.path.exists(tilenametiff):
                        print 'File does not exist: ', tilenametiff
                        sys.exit()
                     elif not os.path.exists(tilenametiffPan):
                        print 'File does not exist: ', tilenametiffPan
                        sys.exit() 

                     # ---- now we need to establish outfile names for pan-sharpened tiff files
                     outputNameTileBrovey = tilenametiff.replace('.tif','_PanSharpenedBrovey.tif')
                     outputNameTileFIHS   = tilenametiff.replace('.tif','_PanSharpenedFIHS.tif')

                     # ----- now we need to convert geotiff tile file to pan-sharpened images
                     dsmulti_tile = gdal.Open(tilenametiff)
                     dspan_tile   = gdal.Open(tilenametiffPan)

                     with warn.catch_warnings():
                        warn.filterwarnings('ignore',category=FutureWarning)

                        imgsBrovey = broveySharpen(dsmulti_tile, dspan_tile)
                        if None not in imgsBrovey:
                           writeImg(imgsBrovey, outputNameTileBrovey, dspan_tile)
                           outputTileNamesBrovey.append(outputNameTileBrovey)
                           del imgsBrovey
                           gc.collect() 

                        imgsFIHS = fihsSharpen(dsmulti_tile, dspan_tile)
                        if None not in imgsFIHS:
                           writeImg(imgsFIHS, outputNameTileFIHS, dspan_tile)
                           outputTileNamesFIHS.append(outputNameTileFIHS)
                           del imgsFIHS
                           gc.collect()

                        if os.path.exists(outputNameTileFIHS) and os.path.exists(outputNameTileBrovey):
                           os.remove(tilenametiff)
                           os.remove(tilenametiffPan)

                     if len(outputTileNamesBrovey)>0 and len(outputTileNamesFIHS)>0 and (len(outputTileNamesBrovey)==len(outputTileNamesFIHS)):

                        # ---- now we need to take all pan-sharpened FIHS/Brovey tiles, and mosaic them ... using gdal_merge
                        mosaicCmdBrovey = gdalMergeLocation+' -o ' + fulloutnamebrovey + ' -of GTiff '
                        mosaicCmdListBrovey = []
                        mosaicCmdListBrovey.extend([mosaicCmdBrovey])
                        mosaicCmdListBrovey.extend(outputTileNamesBrovey)
                        mosaicCmdBrovey = ' '.join(mosaicCmdListBrovey)
                        if not os.path.exists(fulloutnamebrovey): os.system(mosaicCmdBrovey)

                        mosaicCmdFIHS = gdalMergeLocation+' -o ' + fulloutnamefihs + ' -of GTiff '
                        mosaicCmdListFIHS = []
                        mosaicCmdListFIHS.extend([mosaicCmdFIHS])
                        mosaicCmdListFIHS.extend(outputTileNamesFIHS)
                        mosaicCmdFIHS = ' '.join(mosaicCmdListFIHS)
                        if not os.path.exists(fulloutnamefihs): os.system(mosaicCmdFIHS)

                     # ---- clean up some files we don't need anymore
                     for n in range(len(outputTileNamesBrovey)):
                        os.remove(outputTileNamesBrovey[n])
                        os.remove(outputTileNamesFIHS[n])

            except: pass 

if __name__ == '__main__':
    main() 
        
