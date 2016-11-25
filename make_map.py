'''Find KiDS tiles and save as png. Save in directory structure needed
by the Google Maps API to correctly map the images next to each other
in each of the zoom levels.

See example at:
https://developers.google.com/maps/documentation/javascript/examples/maptype-image?hl=nl
'''
import glob
import subprocess
import os
import numpy as np
from datetime import datetime
from datetime import date

import matplotlib as mpl

mpl.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import MapGrid
import MapTile

def modify_images(images_dir, images_dir_mod):
    """Modify images to plot."""
    # Rename directory containing newly downloaded images by replacing
    # '_new'.
    subprocess.call(
      'mv %s %s' % (images_dir, images_dir.replace('_new', '')), shell=True
    )

    images_dir = images_dir.replace('_new', '')

    # Make images directory to store modified images, which are later
    # plotted.
    os.mkdir(images_dir_mod)

    # Copy png's to images directory.
    os.system(
      'cp -rf %s/*.png %s' % (images_dir, images_dir_mod)
    )

    # Convert any jpg's to png, saving in images directory.
    os.chdir(images_dir)

    subprocess.call(
      'mogrify -path %s -format png *.jpg' % images_dir_mod, shell=True
    )

    # Resize to exactly 267x256 since original sizes are 1.045:1.
    # Try resizing to larger size in order to improve image quality.
    os.chdir(images_dir_mod)

    subprocess.call(
      'mogrify -resize 802x768! *.png', shell=True
    )

    # Rename png's according to normalized RA, Dec in range [0, 1].
    images = glob.glob('*.png')

    for i in images:

        new_name_ra = i.split('_')[0]
        new_name_ra = str(round(float(new_name_ra) / 360., 4))

        new_name_dec = i.split('_')[1].replace('.png', '')
        new_name_dec = str(
          round((float(new_name_dec) + 90) / 180., 4)
        )

        new_name = '%s_%s.png' % (new_name_ra, new_name_dec)

        subprocess.call('mv %s %s' % (i, new_name), shell=True)

    os.chdir(main_wd)

def move_image_center(images_dir):
    """Move images with ra <= 60d to ra + 1.5d, in order to better plot
    images around ra = 0d.
    """
    os.chdir(os.path.join(main_wd, images_dir))

    images_move = [
      i for i in glob.glob('*.png') if float(i.split('_')[0]) <= 60/360.
    ]

    for image in images_move:

        new_name_ra = image.split('_')[0]

        new_name_ra = str(float(new_name_ra) + 1.5/360)

        new_name_dec = image.split('_')[1]

        new_name = '%s_%s' % (new_name_ra, new_name_dec)

        subprocess.call(
          'mv %s %s' % (image, new_name), shell=True
        )

    os.chdir(main_wd)

def make_array_images(images_dir):
    """Make list of lists for each of the images.
    
    Each element is a list for each of the images. Each list
    contains in [0] and [1] the normalized RA and Dec, respectively, and
    in [2] the image data read by mpimg.imread().
    
    Return list.
    """
    os.chdir(images_dir)

    imgs = [
      [
      float(i.split('_')[0]), float(i.split('_')[1].replace('.png', '')),
      mpimg.imread(i)
      ] for i in glob.glob('*.png')
    ]

    os.chdir(main_wd)
    
    with open(dir_log, 'a') as fp:
        fp.write('Plotting %i images\n' % len(imgs))

    return imgs

def find_overlap(ra, dec, limit_x, limit_y):
    """Find images within MapTile limits.
    
    The arguments limit_x and limit_y are the limits of the
    MapTile. The arguments ra and dec are the center coordinates
    of the image.
    
    Return True if image + and - extent is within MapTile limits, otherwise
    return False.
    """
    extent_dec = 0.5 / 180
    extent_ra = 0.5 / 360

    if (limit_y[0] <= dec+extent_dec <= limit_y[1]) &\
      (limit_y[0] <= dec-extent_dec <= limit_y[1]) &\
      (limit_x[1] <= ra-extent_ra <= limit_x[0]) &\
      (limit_x[1] <= ra+extent_ra <= limit_x[0]):
        return True

    if (dec+extent_dec >= limit_y[0] >= dec-extent_dec) &\
      (limit_x[1] <= ra-extent_ra <= limit_x[0]) &\
      (limit_x[1] <= ra+extent_ra <= limit_x[0]):
        return True

    elif (dec+extent_dec >= limit_y[1] >= dec-extent_dec) &\
      (limit_x[1] <= ra-extent_ra <= limit_x[0]) &\
      (limit_x[1] <= ra+extent_ra <= limit_x[0]):
        return True

    elif (ra-extent_ra <= limit_x[0] <= ra+extent_ra) &\
      (limit_y[0] <= dec+extent_dec <= limit_y[1]) &\
      (limit_y[0] <= dec-extent_dec <= limit_y[1]):
        return True

    elif (ra-extent_ra <= limit_x[1] <= ra+extent_ra) &\
      (limit_y[0] <= dec+extent_dec <= limit_y[1]) &\
      (limit_y[0] <= dec-extent_dec <= limit_y[1]):
        return True

    elif (ra-extent_ra <= limit_x[1] <= ra+extent_ra):
        if (dec+extent_dec >= limit_y[0] >= dec-extent_dec) or\
          (dec+extent_dec >= limit_y[1] >= dec-extent_dec):
            return True

    elif (ra-extent_ra <= limit_x[0] <= ra+extent_ra):
        if (dec+extent_dec >= limit_y[0] >= dec-extent_dec) or\
          (dec+extent_dec >= limit_y[1] >= dec-extent_dec):
            return True

    else:
        return False

def make_col(col, num_tiles, num_rows, ra_borders, dec_borders, zoom_level, imgs):
    """Make a column of the map.
    
    Makes a directory named col, in which the png's will be saved.
    
    To speed things up, use an increment and a counter. The increment
    is equal to the larger of 16 or num_rows. Inside the while loop,
    the for loop runs in the range within the counter and the counter
    plus the increment. The while loop takes care to run for all num_rows.
    """
    start_col = datetime.now()
    
    try:
        os.mkdir(str(col))
    except:
        pass

    os.chdir(str(col))

    limit_x = (ra_borders[col],
      ra_borders[col] - 1. / (num_tiles/2**zoom_level))

    inc2 = 16
    if num_rows < 16:
        inc2 = num_rows

    counter2 = 0
    while counter2 < num_rows:
        for row in range(counter2, counter2+inc2):
            try:
                make_row(col, row, num_tiles, limit_x, dec_borders, zoom_level, imgs)
            except Exception, e:
                with open(dir_log, 'a') as fp:
                    fp.write(
                      'col %s fn make_row %s excepted %s\n' %\
                      (str(col), str(row), str(e))
                    )
                pass

        counter2 += inc2

    os.chdir(os.path.join(public_dir, str(zoom_level)))

def make_row(col, row, num_tiles, limit_x, dec_borders, zoom_level, imgs):
    """Make a row of the map.
    
    Plots and saves a png, to show all images within limit_x and
    the vertical limit, which is calculated using dec_borders.
    
    If no images are within the limits then an empty png will be
    saved.
    """
    limit_y = (dec_borders[row],
      dec_borders[row] + 1. / (num_tiles/2**zoom_level))

    grid = MapGrid()
    grid.set_limit_x(limit_x)
    grid.set_limit_y(limit_y)

    grid.make()

    images_plot = [
      i for i in imgs if
      find_overlap(i[0], i[1], limit_x, limit_y)
    ]

    if len(images_plot):
        tile = MapTile()
        tile.set_image_list(images_plot)
        tile.set_file_name(str(row)+'.png')
        tile.set_main_wd(main_wd)
        tile.set_cwd(os.getcwd())
        tile.set_images_dir(main_wd + '/images')
        tile.make(show=False)
    else:
        grid.set_file_name(str(row)+'.png')
        grid.save()

    grid.close_fig()

def make_tile(zoom_level, imgs):
    """Make a tile of the map."""
    start_time_2 = datetime.now()

    # Check if a directory named as zoom_level exists, if not create
    # one.  Delete variable containing directory names to save memory.
    zoom_dir = os.path.join(public_dir, str(zoom_level))
    
    #if os.path.join(public_dir, str(zoom_level)) not in zoom_dirs:
    if not os.path.isdir(zoom_dir):

        os.mkdir(zoom_dir)

    os.chdir(zoom_dir)

    # Make variable to hold total number of tiles at zoom_level.
    num_tiles = 2 ** (zoom_level * 2)
    
    # Also the number of columns and rows, which should be equal.
    num_col_dirs = num_tiles / 2**zoom_level
    num_rows = num_col_dirs

    # Make numpy arrays to contain the larger (smaller) borders for RA
    # (Dec).  The borders are used as limits to determine which images
    # lie within them and should then be plotted in a tile.
    ra_borders = np.arange(1, 0, -1. / (num_tiles/2**zoom_level))
    
    dec_borders = np.arange(0, 1, 1. / (num_tiles/2**zoom_level))

    # Speed up script by running for loop 16 times, or for smaller
    # zooms a number of times equal to the number of columns.
    inc = 16
    
    if num_col_dirs < 16:
        inc = num_col_dirs

    counter = 0
    
    while counter < num_col_dirs:
        
        for col in range(counter, counter+inc):
        
            try:
                make_col(col, num_tiles, num_rows, ra_borders, dec_borders, zoom_level, imgs)
        
            except Exception, e:
        
                with open(dir_log, 'a') as fp:
                    fp.write(
                      'fn make_col %s excepted %s\n' %\
                      (str(col), str(e))
                    )
                pass

        counter += inc

    os.chdir(main_wd)
    
    with open(dir_log, 'a') as fp:
        message = 'Zoom %i took: %s\n' %\
          (zoom_level, str(datetime.now()-start_time_2))
        
        fp.write(message)
        
        print message

def main(is_modify_images=True):
    imgs = None
    
    start_time = datetime.now()

    # Remove any logs made on the same day as when the script is running.
    if glob.glob(dir_log):
        subprocess.call('rm -rf %s' % dir_log, shell=True)

    max_zoom = 9

    # Modify the images to plot. Only needs to run once on images.
    if os.path.isdir(dir_images_new):
        if is_modify_images == True:
            try:
                modify_images(dir_images_new, dir_images_modified)

            except Exception, e:

                with open(dir_log, 'a') as fp:
                    fp.write(
                      'fn modify_images excepted %s\n' % str(e)
                    )
                    
                raise SystemExit

    if os.path.isdir(dir_images_modified):
        # Move the image center. Only needs to run once.
        if is_modify_images == True:
            try:
                move_image_center(dir_images_modified)
        
            except Exception, e:
        
                with open(dir_log, 'a') as fp:
                    fp.write(
                      'fn move_image_center excepted %s\n' % str(e)
                    )
        
                raise SystemExit

        try:
            imgs = make_array_images(dir_images_modified)
    
        except Exception, e:
    
            with open(dir_log, 'a') as fp:
                fp.write(
                  'fn make_array_images excepted %s\n' % str(e)
                )
    
            raise SystemExit

    if imgs != None:
        if len(imgs) > 0:
            for zoom_level in np.arange(0, max_zoom+1, 1):
        
                try:
                    make_tile(zoom_level, imgs)

                except Exception, e:

                    with open(dir_log, 'a') as fp:
                        fp.write(
                          'fn make_tile %s excepted %s\n' %\
                          (str(zoom_level), str(e))
                        )
                        
                    pass

        else:
            with open(dir_log, 'a') as fp:
                fp.write(
                  'no images to plot %s\n' % len(imgs)
                )

    else:
        with open(dir_log, 'a') as fp:
            fp.write(
              'no directory with images found\n'
            )

            
    with open(dir_log, 'a') as fp:

        fp.write('Full script took: %s' % str(datetime.now()-start_time))
    
if __name__ == '__main__':

    filename_log = '%s-make_map.log' %\
      date.today().isoformat().replace('-', '')

    main_wd = os.getcwd()

    dir_log = os.path.join(main_wd, filename_log)

    # Public directory that can be accessed from the Internet,
    # to hold output of this script.
    public_dir = '/PATH/TO/public_html/kidsmap'

    # Directory that holds images to plot.
    dir_images_new = os.path.join(main_wd, 'images_big_new')
    
    # Directory where modified images will be saved.
    dir_images_modified = os.path.join(main_wd, 'images')

    main(is_modify_images=False)
