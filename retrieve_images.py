from astro.main.RegriddedFrame import CoaddedRegriddedFrame
from astro.main.InspectFigure import InspectFigure
from astro.main.RawFrame import RawScienceFrame

import pickle
import glob
import subprocess
import os
from datetime import date
import datetime

def find_last_file(filename):
    """Search current directory for a file.

    Argument string filename is the file to search for.

    Glob files created by this script, then sort and take
    the last one.

    Return datetime object or string.
    """
    filenames_log = glob.glob(filename)
    filenames_log.sort()
    filenames_log = list(filenames_log)[-1]

    # Keep the part of the filename that gives the date.
    # Return datetime.datetime object with [0] = year, [1] = month,
    # [2] = day.
    if 'retrieve_images.log' in filename:
        filenames_log = filenames_log[:filenames_log.find('-')]
        return datetime.datetime(
          int(filenames_log[:4]), int(filenames_log[4:6]),
          int(filenames_log[6:])
        )

    elif 'coadds.pkl' in filename:
        return filenames_log

def do_query_raw():
    """Query AWE for desired RawScienceFrames.

    Makes a list of a set of all observing_block.name. List is dumped to
    pickle file for
    future reference. Its length is written to log file.

    Return list.
    """
    # Find date of last log file
    #date_log = find_last_file('*retrieve_images.log')

    query_raw =\
      (RawScienceFrame.observing_block.name.like("KIDS_*_*_i")) &\
      (RawScienceFrame.is_valid > 1) &\
      (RawScienceFrame.chip.name == "ESO_CCD_#76") #&\
      #!!!(RawScienceFrame.creation_date >= date_log)

    ob_names = list(
      set(
      [raw.observing_block.name for raw in query_raw]
      )
    )
    ob_names.sort()

    # Keep list of all observing_block.name in pickle file,
    # for future reference.
    filename_pkl = '%s-ob_names.pkl' %\
      date.today().isoformat().replace('-', '')

    pickle.dump(ob_names, open(os.path.join(main_wd, filename_pkl), 'wb'))

    # Write to log file length of list with all observing_block.name
    with open(dir_log, 'a') as fp:
        fp.write('ob_names has len %i\n' % len(ob_names))

    return ob_names

def find_coadd(name):
    """Query AWE to find latest Coadd with given name.

    Argument name is an observing_block.name attribute.

    Commented lines are useful for redoing the map. Read creation_date 
    for given name from pickle file.
    If older that date from query, then continue with query. If
    is_on_dataserver, return the Coadd; else write to log file name.
    Else take coadd and find InspectFigure name. If image not downloaded,
    return the coadd; else dump to coadd pickle file the given name and
    the old date, which is actually current.
    """
    coadd = (CoaddedRegriddedFrame.observing_block.name == name).max('creation_date')

    #coadd_dates = [i.creation_date for i in coadd]
    #coadd_dates.sort()

    #date_old = [
      #i.split(',')[1].split(' ') for i in coadds_old if i.split(',')[0] == name
    #][0]
    #date_old = [
      #i for i in list(date_old) if len(i) > 0
    #]
    #date_old = [int(i) for i in date_old[0].split('-')] +\
      #[int(i) for i in date_old[1].split(':')]
    #date_old = datetime.datetime(
      #date_old[0], date_old[1], date_old[2], date_old[3], date_old[4],
      #date_old[5]
    #)

    #if date_old < coadd_dates[-1]:
        #coadd = [
          #i for i in list(coadd) if i.creation_date == coadd_dates[-1]
        #]
        #if coadd[0].is_on_dataserver():
            #return coadd[0]
        #else:
            #with open(dir_log, 'a') as fp:
                #fp.write('Coadd %s is_on_dataserver False\n' % name)
            #return

    #else:
        #coadd = [
          #i for i in list(coadd) if i.creation_date == coadd_dates[-1]
        #]

    #fig = InspectFigure.select(coadd[0], subtype = 'Thumbnail')

    #image_name = coadd[0].OBJECT.replace('KIDS_', '') + fig[0].filename[-4:]

    #if image_name not in image_files:
        #if coadd.is_on_dataserver():
            #return coadd
        #else:
            #with open(dir_log, 'a') as fp:
                #fp.write('Coadd %s is_on_dataserver False\n' % name)
            #return
    #else:
        #line = '%s, %s' % (name, date_old)
        #pickle.dump(line, open(dir_pkl_coadds, 'ab'))
        #return
    
    return coadd

def download_image(coadd):
    """Query AWE for Thumbnail InspectFigure of coadd.
    
    Argument coadd is a CoaddedRegriddedFrame object.

    If is_on_dataserver, take the figure and make variable to hold
    desired image_name, which is the downloaded image's filename.
    If image_name is not already downloaded then get it and rename it.
    Else write to log file coadd.
    
    Return True for retrieved, otherwise False.
    """
    fig = InspectFigure.select(coadd, subtype = 'Thumbnail')

    if fig[0].is_on_dataserver():
        fig = fig[0]
        image_name = coadd.OBJECT.replace('KIDS_', '') + fig.filename[-4:]

        os.chdir(dir_new)

        fig.retrieve()

        subprocess.call(['mv', fig.filename, image_name])

        line = '%s, %s' %\
          (coadd.observing_block.name, str(coadd.creation_date))

        pickle.dump(line, open(dir_pkl_coadds, 'ab'))

        os.chdir(main_wd)
        return True

    else:
        with open(dir_log, 'a') as fp:
            fp.write(
              'InspectFigure %s is_on_dataserver False\n' % coadd.filename
            )
        return False

if __name__ == '__main__':
    main_wd = os.getcwd()

    # Directory that contains images currently on map.
    # If first time making the map, then this directory does not exist.
    dir_old = os.path.join(main_wd, 'images_big')

    # Directory that will contain new images.
    dir_new = os.path.join(main_wd, 'images_big_new')

    # Location of log file with info about number of observing_block.name and
    # which InspectFigures could not be downloaded.
    filename_log = '%s-retrieve_images.log' %\
      date.today().isoformat().replace('-', '')

    dir_log = os.path.join(main_wd, filename_log)

    # Remove any logs with same filename.
    try:
        subprocess.call('rm -rf %s' % dir_log, shell=True)
    except:
        pass

    # Location of pickle file with info about observing_block.name and Coadd
    # creation_date, for InspectFigures that have been retrieved.
    filename_log = '%s-coadds.pkl' %\
      date.today().isoformat().replace('-', '')
    dir_pkl_coadds = os.path.join(main_wd, filename_log)

    # Remove any files with same filename.
    try:
        subprocess.call('rm -rf %s' % dir_pkl_coadds, shell=True)
    except:
        pass

    # Useful when redoing the map, to check if there are Coadds not on
    # the map.
    #coadds_old = []
    #with open(find_last_file('*coadds.pkl'), 'rb') as fp:
        #while 1:
            #try:
                #coadds_old.append(
                  #pickle.load(fp)
                #)
            #except EOFError:
                #break
            #except:
                #pass
    # Glob image files currently displayed
    #image_files = glob.glob(dir_old+'/*')

    try:
        ob_names = do_query_raw()

    except Exception, e:
        with open(dir_log, 'a') as fp:
            fp.write('Raw query excepted %s\n' % str(e))

            raise SystemExit

    if not glob.glob(dir_new):
        os.mkdir(dir_new)

    new_images = False

    for name in ob_names:

        try:
            coadd = find_coadd(name)

        except Exception, e:
            with open(dir_log, 'a') as fp:
                fp.write('Coadd query for %s excepted: %s\n' % (name, str(e)))
            continue

        try:
            if coadd:
                new_images = download_image(coadd)

            else:
                continue

        except Exception, e:
            with open(dir_log, 'a') as fp:
                fp.write(
                  'Figure query for %s excepted: %s\n' %\
                  (coadd.filename, str(e))
                )
            continue

    # If no new images downloaded, then remove directory made to contain
    # them. Else copy all previous images to directory with new ones.
    if not new_images:
        subprocess.call('rm -rf %s' % dir_new, shell=True)
    else:
        subprocess.call('cp -rf %s/* %s' % (dir_old, dir_new), shell=True)
