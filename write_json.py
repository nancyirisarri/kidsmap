'''Write JSON format file containing info about the KiDS tiles. The
file is loaded with JavaScript and the Google Maps API.

See example at:
https://developers.google.com/maps/documentation/javascript/importing_data
'''
from astro.main.RegriddedFrame import CoaddedRegriddedFrame
from astro.main.InspectFigure import InspectFigure
from common.log.Comment import Comment

import pickle
import glob
import subprocess
import os
import numpy as np
from datetime import datetime
        
main_wd = os.getcwd()

os.chdir('images')

images = glob.glob('*.png')

os.chdir(main_wd)

# Load file created by make_map.py that contains observing block names
# that were available when that script ran.
ob_names = pickle.load(open(glob.glob('*ob_names.pkl')[0], 'rb'))

ob_names.sort()

# For each of the ob_names, rename ra and dec to range 0-1 in order to 
# have same names as done by make_map.py. Then if ra <= 60/360. move
# it to +1.5/360. Finally if the renamed ob_name is in list images, we
# should have plotted it and it should be added to ob_names_final in
# order to further be processed.
ob_names_final = []

for i in ob_names:
    new_name = i.replace(
      i.split('_')[1], str(round(float(i.split('_')[1]) / 360., 4))
    )

    new_name = new_name.replace(
      new_name.split('_')[2],
      str(round(
      (float(new_name.split('_')[2]) + 90) / 180.,
      4))
    )

    new_name = new_name.replace('KIDS_', '').replace('_i', '.png')

    if float(new_name.split('_')[0]) <= 60/360.:
        new_name = new_name.replace(
          new_name.split('_')[0], str(float(new_name.split('_')[0]) + 1.5/360)
        )
        
    if new_name in images:
        ob_names_final.append(i)

def get_comments(object_in):
    """Get comments for object_in."""
    try:
        comments = [
          c.content for c in Comment.getCommentsObject(object_in)
          ]
        comments = [i.replace(';', ',') for i in comments]

        comments_final = []
        for comment in comments:
            comment_split = comment.split(',')
            comment_split = [i.replace('\n', '') for i in comment_split]
            comments_final += comment_split
        
        if len(comments_final):
            string = ''
            for i in comments_final:
                string += i + ','
            return string
        else:
            return 'No comments found,'

    except:
        return 'No comments found,'
      
if __name__ == '__main__':
    # ob = ObservingBlock
    # rsf = RawScienceFrame
    # coadd = CoaddedRegriddedFrame
    # coordinates = [x, y] = [abs(ra-180), dec*(28.7/15)]

    prestring_db = 'http://ds.astro.rug.astro-wise.org:8000/'

    if glob.glob('data.json'):
        try:
            subprocess.call(
                'mv %s %s' % (glob.glob('data.json')[0], 'archive/'), shell=True
            )
        except Exception, e:
            print 'Could not move data.json file, %s' % str(e)
            print '\nMaking a new one.'

    json_file = open('data.json', 'w')

    json_start = '''{ "type": "FeatureCollection",
 "features": ['''
    json_file.write(json_start)

    json_format = '''
   { "type": "Feature",
     "properties": {
       "info": "ObservingBlock name: %s, ObservingBlock start: %s, Coadd is_valid: %s, Coadd imstat_max: %s, RSF is_valid: e.g., RSF airmend: e.g.",
       "image": "%s%s",
       "obName": "%s", 
       "obStart": "%s", 
       "coaddIsValid": "%s",
       "coaddImstatMax": "%s",
       "coaddComments": "%s",
       "rsfIsValid": "e.g.", 
       "rsfAirmend": "e.g." 
     },
     "geometry": {
       "type": "Point",
       "coordinates": [%s, %s]
     }
   },'''

    for i in range(len(ob_names_final)):        
        coadd = (
          CoaddedRegriddedFrame.observing_block.name == ob_names_final[i]
        ).max('creation_date')

        try:
            x = coadd.filename
        except:
            print 'not found %s' % ob_names_final[i]
        
        coadd_comments = get_comments(coadd)

        fig = InspectFigure.select(coadd, subtype='Thumbnail')
        
        try:
            fig_filename = fig[0].filename
        
        except:
            fig_filename = ''
        
        ra = float(coadd.observing_block.name.split('_')[1])
        
        if ra <= 60.:
            ra += 1.5
        
        ra = 180 - ra
            
        dec = float(coadd.observing_block.name.split('_')[2])
        
        if (dec < -15.) & (dec > -30.):
            dec = -1.5 * np.abs(26.2 + dec) - 46.

        elif (dec < -30.) & (dec > -32.):
            dec = -1.5 * np.abs(30.2 + dec) - 51.5

        elif (dec < -32.):
            dec = -1. * np.abs(32.2 + dec) - 54

        else:
            dec *= (28.7 / 15)

        try:
            coadd_observing_block_name = coadd.observing_block.name

        except:
            coadd_observing_block_name = 'N/A'
        
        try:
            coadd_observing_block_start = coadd.observing_block.start

        except:
            coadd_observing_block_start = 'N/A'
            
        try:
            coadd_is_valid = coadd.is_valid

        except:
            coadd_is_valid = 'N/A'
            
        try:
            coadd_imstat_max = str(coadd.imstat.max)

        except:
            coadd_imstat_max = 'N/A'

        to_write = json_format % (coadd_observing_block_name, 
          coadd_observing_block_start, coadd_is_valid, 
          coadd_imstat_max, prestring_db, fig_filename,
          coadd_observing_block_name, 
          coadd_observing_block_start, coadd_is_valid, 
          coadd_imstat_max, coadd_comments, str(ra), str(dec))

        if i == range(len(ob_names_final))[-1]:
            to_write_2 = to_write[:-2] + to_write[-2:].replace(',', '')

            json_file.write(to_write_2)
        
        else:
            json_file.write(to_write)        

    json_finish = '''  
 ]
}'''
    json_file.write(json_finish)

    json_file.close()

