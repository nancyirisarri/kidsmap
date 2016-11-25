from datetime import datetime
import subprocess
import os

import matplotlib.pyplot as plt

plt.ioff()

class MapTile:
    """Draws InspectFigures on a grid.
    
    Used when there are images with RA and DEC within the current limits.
    """
    def __init__(self):
        self.width = 0.5 / 360
        self.height = 0.5 / 180
        self.cmap = 'gist_gray'
        self.file_name = 'map_new.png'
        self.dpi = 100
        self.image_list = []
        self.main_wd = ''
        self.cwd = ''
        self.images_dir = ''
        
    def set_width(self, width):
        self.width = width
        
    def set_height(self, height):
        self.height = height
        
    def set_cmap(self, cmap):
        self.cmap = cmap
        
    def set_file_name(self, name):
        self.file_name = name
        
    def set_dpi(self, dpi):
        self.dpi = dpi
                
    def add_image(self, image):
        self.image_list.append(image)
        self.image_list = set(self.image_list)
        self.image_list = list(self.image_list)
        
    def set_image_list(self, image_list):
        self.image_list = image_list

    def set_main_wd(self, main_wd):
        self.main_wd = main_wd
        
    def set_cwd(self, cwd):
        self.cwd = cwd

    def set_images_dir(self, images_dir):
        self.images_dir = images_dir

    def make(self, show=False, resize=False):
        os.chdir(os.path.join(self.main_wd, self.images_dir))

        for image in self.image_list:

            plt.ioff()

            plt.imshow(
              image[2], cmap = self.cmap, extent=(image[0]-self.width, 
              image[0]+self.width, image[1]-self.height,
              image[1]+self.height)
            )

        if show:
            plt.show()

        os.chdir(self.cwd)

        plt.tight_layout(pad=0.0, w_pad=0.0, h_pad=0.0)

        plt.savefig(
          self.file_name, dpi=self.dpi, format='png',
          bbox_inches='tight', pad_inches=0, 
          facecolor='0.8', edgecolor='none'
        )

        if resize:
            subprocess.call(
              'mogrify -resize 256x256! %s' % self.file_name, shell=True
            )
