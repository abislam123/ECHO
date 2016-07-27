#! /usr/bin/env python
'''

    Author: Jacob Burba

    ECHO_plot.py does useful things for some and pointless things for others.  Such is life.
    --lat0 and --lon0 optional

'''

#from matplotlib import use
#use('TkAgg')
from ECHO_read_utils import get_data
from ECHO_plot_utils import animate_spectrum

import matplotlib.gridspec as gridspec
import optparse,sys,warnings
import numpy as np
import matplotlib.pyplot as plt


o = optparse.OptionParser()
o.set_description('Queries ground station server for interpolated GPS position')
o.add_option('--spec_file',type=str,help='Accumulated file for plotting')
o.add_option('--freq',type=float,default=137.5,help='Peak frequency to look for in data')
o.add_option('--width',type=int,default=500,help='Number of channels to include in spectrum analysis')
opts,args = o.parse_args(sys.argv[1:])


fmin,fmax = int(opts.freq)-1,int(opts.freq)+1 # MHz; for plotting

# Get initial data from Signal Hound
spec_times,spec_raw,freqs,freq_chan = get_data(opts.spec_file,filetype='sh',freq=opts.freq,width=opts.width)
print spec_times.shape,spec_raw.shape,freqs.shape
freq_chan = np.where(np.abs(freqs-opts.freq).min()==np.abs(freqs-opts.freq))[0]
print 'Frequency plotting: %.3f' %freqs[freq_chan]
freqs -= 0.005
#print freqs.shape,spec_raw.shape
if spec_times.shape[0] == 0: # Ensure data in inFile
    print 'Invalid data: array with zero dimension\nExiting...\n'
    sys.exit()

# Initialize plotting figure
fig = plt.figure(figsize=(16,9),dpi=80,facecolor='w',edgecolor='w')
#mng = plt.get_current_fig_manager() # Make figure full screen
fig.suptitle('ECHO Realtime Spectrum: %s' %opts.spec_file,fontsize=16)

# Spectrum plot initialization
gsl = gridspec.GridSpec(1,1) # Sets up grid for placing plots
spec_plot = fig.add_subplot(gsl[0]) # Initialize the spectrum plot in figure
spec_line, = spec_plot.plot(freqs,spec_raw[0,:])
#freq_labels = [freqs[0],freqs[9],freqs[10],freqs[11],freqs[-1]]
#plt.xticks(freq_labels,map(str,freq_labels),rotation=45)
spec_plot.set_xlabel("Frequency [Mhz]")
spec_plot.set_ylabel("Power [dBm]")
spec_plot.set_ylim([-90,-45])
spec_plot.set_xlim([freqs[0],freqs[-1]])
spec_plot.axvline(x=137.500,ymin=-100,ymax=10)

with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    # This raises warnings since tight layout cannot
    # handle gridspec automatically. We are going to
    # do that manually so we can filter the warning.
    gsl.tight_layout(fig, rect=[0, 0, 1.0, 0.97])


plt.subplots_adjust(top=0.8)
#mng.window.state('zoomed')
plt.draw()
plt.show(block=False)

try:
    plot_ind = 0
    while True:
        # Get updated data from Signal Hound
        spec_times,spec_raw,freqs,freq_chan = get_data(opts.spec_file,filetype='sh',freq=opts.freq,width=opts.width)

        while plot_ind < spec_times.shape[0]:
            # Update plotting window
            animate_spectrum(plot_ind,spec_plot,spec_line,spec_raw)

            plt.pause(0.00001)
            plot_ind += 1

except (KeyboardInterrupt):
    print '\nExiting...\n'
    sys.exit()
