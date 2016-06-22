import numpy as np
from astropy.time import Time

from ECHO_time_utils import flight_time_filter,waypt_time_filter

SEC_PER_WEEK = 604800

def get_data(infile,filetype=None,freqs=[],freq=0.0,freq_chan=None,
             ant=None,dip=None,width=100,isList=False,times=None,waypts=None):

    if filetype == 'gps':
        gps_arr = []
        if not isList:
            gps_files = [infile]
        else:
            gps_files = []
            lines = open(infile).readlines()
            for line in lines:
                gps_files.append(line.rstrip('\n'))
        for gps_file in gps_files:
            lines = open(gps_file).readlines()
            if not len(lines) == 0:
                for line in lines:
                    if line.startswith('#'):
                        continue
                    line = line.rstrip('\n').split(',')
                    if len(line) == 4: # Make sure line has finished printing
                        gps_arr.append(map(float,line))
        gps_arr = np.array(gps_arr)
        gps_times,lats,lons,alts = np.split(gps_arr,
                                            [1,2,3],
                                            axis=1)
        gps_times = Time(gps_times,format='gps')
        lats = lats.squeeze()
        lons = lons.squeeze()
        alts = alts.squeeze()
        '''
        gps_arr = [map(float,line.rstrip('\n').split(','))\
        for line in lines[2:] if len(line.split(','))==4 and\
        not line.startswith('#')]
        '''
        return gps_times,lats.squeeze(),lons.squeeze(),alts.squeeze()

    elif filetype == 'apm':
        lats,lons,alts = [],[],[]
        weektimes = []
        if not isList:
            apm_files = [infile]
        else:
            apm_files = []
            lines = open(infile).readlines()
            for line in lines:
                apm_files.append(line.rstrip('\n'))
        for apm_file in apm_files:
            lines = open(apm_file).readlines()
            if not len(lines) == 0:
                for line in lines:
                    if line.startswith('GPS'):
                        lats.append(map(float,line.split(',')[7:8]))
                        lons.append(map(float,line.split(',')[8:9]))
                        alts.append(map(float,line.split(',')[9:10]))
                        weektimes.append(map(float,line.split(',')[3:5])) #ms and week number
        weektimes = np.array(weektimes)
        apm_times = weektimes[:,1]*SEC_PER_WEEK+weektimes[:,0]/1000.
        apm_times = Time(apm_times,format='gps')
        lats = np.array(lats).squeeze()
        lons = np.array(lons).squeeze()
        alts = np.array(alts).squeeze()
        return apm_times,lats,lons,alts

    elif filetype == 'sh':
        spec_times = []
        spec_raw = []
        if not isList:
            spec_files = [infile]
        else:
            spec_files = []
            lines = open(infile).readlines()
            for line in lines:
                spec_files.append(line.rstrip('\n'))
        for spec_file in spec_files:
            lines = open(spec_file).readlines()
            if not len(lines) == 0:
                if len(freqs) == 0:
                    freqs = np.array(map(float,lines[1].rstrip('\n').split(',')[1:]))
                    # Get index of freq for gridding
                    freq_chan = np.where(np.abs(freqs-freq).min()==np.abs(freqs-freq))[0]
                    # Filter freqs around freq_chan
                    freqs = freqs[freq_chan-width:freq_chan+width]
                for line in lines:
                    if line.startswith('#'):
                        continue
                    line = line.rstrip('\n').split(',')
                    if len(line) == 4097: # Make sure line has finished printing
                        spec_times.append(float(line[0]))
                        spec_raw.append(map(float,line[freq_chan-width:freq_chan+width]))
        spec_times = Time(spec_times,format='unix')
        spec_raw = np.array(spec_raw)
        freqs = np.array(freqs).squeeze()
        return spec_times,spec_raw,freqs,freq_chan

    elif filetype == 'echo':
        all_Data = []
        freqs = []
        lines = open(infile).readlines()
        lat0,lon0 = map(float,lines[2].rstrip('\n').split(':')[1].strip(' ').split(','))
        freqs = map(float,lines[3].rstrip('\n').split(':')[1].strip(' ').split(','))
        #freqs = np.array(freqs)
        for line in lines:
            if line.startswith('#'):
                continue
            line = line.rstrip('\n').split(',')
            if len(line) == (len(freqs)+4):
                if not line[1] == '-1':
                    all_Data.append(map(float,line))
        all_Data = np.array(all_Data)

        # If start/stop times passed, filter data
        if not times is None:
            #print 'Reading in file %s...' %times
            inds = flight_time_filter(times,all_Data[:,0])
            #print 'Before start/stop time filter: %s' %all_Data.shape[0]
            all_Data = all_Data[inds]
            #print 'After start/stop time filter: %s' %all_Data.shape[0]

        # If waypoint time passed, filter data
        if not waypts is None:
            inds = waypt_time_filter(waypts,all_Data[:,0])
            #print 'Before waypt time filter: %s' %all_Data.shape[0]
            all_Data = all_Data[inds]
            #print 'After waypt time filter: %s' %all_Data.shape[0]

        #spec_times,lats,lons,alts,spec_raw = np.split(all_Data,
        #                                              [1,2,3,4],
        #                                              axis=1)
        spec_times,lats,lons,alts,spec_raw = (all_Data[:,0],all_Data[:,1],\
                                         all_Data[:,2],all_Data[:,3],\
                                         all_Data[:,4:])
        spec_times = Time(spec_times,format='gps')
        lats = lats.squeeze(); lats = np.insert(lats,0,lat0)
        lons = lons.squeeze(); lons = np.insert(lons,0,lon0)
        alts = alts.squeeze()
        return spec_times,spec_raw,freqs,lats,lons,alts#,lat0,lon0

    elif filetype == 'orbcomm':
        all_Data = []
        lines = open(infile).readlines()
        for line in lines[:]: # Data begins on fifth line of accumulated file
            if line.startswith('#'):
                continue
            elif not line.split(',')[1] == '-1':
                all_Data.append(map(float,line.rstrip('\n').split(',')))
        all_Data = np.array(all_Data)
        spec_times,lats,lons,alts,yaws = (all_Data[:,1],all_Data[:,2],\
                                          all_Data[:,3],all_Data[:,4],\
                                          all_Data[:,5])
        if ant == 'N':
            lat0,lon0 = (38.4248532,-79.8503723)
            if 'NS' in inFile:
                spec_raw = all_Data[:,12:17] # N antenna, NS dipole
            if 'EW' in inFile:
                spec_raw = all_Data[:,24:29] # N antenna, EW dipole
        elif ant == 'S':
            lat0,lon0 = (38.4239235,-79.8503418)
            if 'NS' in inFile:
                spec_raw = all_Data[:,6:11] # S antenna, NS dipole
            if 'EW' in inFile:
                spec_raw = all_Data[:,18:23] # S antenna, EW dipole
        spec_times = Time(spec_times,format='gps')
        lats = lats.squeeze()
        lons = lons.squeeze()
        alts = alts.squeeze()
        yaws = yaws.squeeze()
        return spec_times,spec_raw,lats,lons,alts,yaws

    elif filetype == 'start-stop':
        time_ranges = []
        lines = open(infile).readlines()
        for line in lines:
            if line.startswith('#'):
                continue
            line = line.rsrtip('\n').split(' ')
            if not len(line) == 0:
                time_ranges.append(map(float,line[0:2]))
        time_ranges = np.array(time_ranges).squeeze()
        return time_ranges

    elif filetype == 'waypts':
        waypt_times = []
        lines = open(infile).readlines()
        for line in lines:
            if line.startswith('#'):
                continue
            line = line.rstrip('\n')
            waypt_times.append(line)
        waypt_times = np.array(waypt_times).squeeze()
        return waypt_times


    else:
        print '\nNo valid filetype found for %s' %infile
        print 'Exiting...\n\n'
        sys.exit()
