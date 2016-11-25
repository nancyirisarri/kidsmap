import subprocess

import numpy as np

#import matplotlib as mpl

#mpl.use('Agg')

import matplotlib.pyplot as plt

plt.ioff()

class MapGrid:
    """Draws lines and background for the current RA/DEC limits.
    
    On top of this the images are drawn by the class MapTile.
    """
    def __init__(self):
        self.lines_dec = np.arange(0., 1.1, 1 / 12.)
        self.lines_ra = np.arange(1., -0.1, -1 / 12.)
        self.digits_dec = []
        self.digits_dec_loc = 0.
        self.digits_ra = []
        self.digits_ra_loc = -90.
        self.limit_x = [0, 360]
        self.limit_y = [-90, 90]
        self.dpi = 100
        self.file_name = '0.png'

    def set_lines_dec(self, min_dec, max_dec, inc_dec):
        self.lines_dec = np.arange(min_dec, max_dec, inc_dec)
        
    def set_lines_ra(self, min_dec, max_dec, inc_dec):
        self.lines_ra = np.arange(max_ra, min_ra, inc_ra)
    
    def set_digits_dec(self, list_digits_dec, digits_dec_loc):
        self.digits_dec = list_digits_dec
        self.digits_dec_loc = digits_dec_loc
    
    def set_digits_ra(self, list_digits_ra, digits_ra_loc):
        self.digits_ra = list_digits_ra
        self.digits_ra_loc = digits_ra_loc
    
    def set_limit_x(self, limit_x):
        self.limit_x = limit_x
    
    def set_limit_y(self, limit_y):
        self.limit_y = limit_y
        
    def set_dpi(self, dpi):
        self.dpi = dpi

    def set_file_name(self, name):
        self.file_name = name
    
    def save(self, resize=False):
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

    def set_fig(self, fig):
        self.fig = fig

    def close_fig(self):
        self.fig.clf()
        
        plt.close()
    
    def make(self, show=False):
        plt.ioff()
        
        fig, ax = plt.subplots(figsize = (2.56, 2.56))

        self.set_fig(fig)

        ax.axis('off')

        #plt.rc('text', usetex = True)
        #plt.rc('font', size = 10)

        for line in self.lines_dec:
            ax.hlines(
              line, 0., 1., color='0.3', linestyle='-', linewidth=0.5, 
              alpha=0.1
            )
              
        for line in self.lines_ra:
            ax.vlines(
              line, 0., 1., color='0.3', linestyle='-', linewidth=0.5,
              alpha=0.1
            )
    
        for digit in self.digits_dec:
            [X, Y] = self.digits_dec_loc, digit

            # To place digits with a minus sign a bit more inside
            # than digits w/o a minus sign.
            if (digit < 0.):
                ax.text(
                  X+5, Y+1, '$%.0f^\circ$'%digit, fontsize=6,
                  horizontalalignment='left'
                )
                
            else:
                ax.text(
                  X, Y+1, '$%.0f^\circ$'%digit, fontsize=6,
                  horizontalalignment='left'
                )
        
        for digit in self.digits_ra:
            
            [X, Y] = digit, self.digits_ra_loc
            
            ax.text(
              X, Y, '$%.0f^\circ$'%digit, fontsize=6,
              horizontalalignment='left'
            )
        
        plt.xticks([])
        
        plt.yticks([])
                
        plt.xlim(self.limit_x[0], self.limit_x[1])
        
        plt.ylim(self.limit_y[0], self.limit_y[1])

        if show:
            plt.show()
