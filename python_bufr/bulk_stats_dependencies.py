import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib import colors 
import copy
import cartopy
import cartopy.feature as cfeat
import cartopy.crs as ccrs
#
# General Purpose Functions
#   can_float                Returns True if input can be converted to a float, otherwise returns False
#   spddir_to_uwdvwd         Converts (spd,dir) to (u,v)
#   truncate_colorbar        Returns colorbar only covering subspace within [0. 1.] of input colorbar
#
def can_float(element: any) -> bool:
    # Determins if an input element can be converted to a float, returns if True or False
    try:
        float(element)
        return True
    except ValueError:
        return False

def spddir_to_uwdvwd(spd,ang):
    import numpy as np
    uwd=-spd*np.sin(ang*(np.pi/180.))
    vwd=-spd*np.cos(ang*(np.pi/180.))
    return uwd, vwd

def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    import numpy as np
    import matplotlib.cm as cm
    from matplotlib import colors
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap

def ob_density_plot(ob_lat,ob_lon,ob_pre,lat_rng,lon_rng,figax):
    # Generates a heatmap of observation density by latitude and longitude
    # Splits into 2 heatmaps for upper- vs lower-tropospheric ob density based on pressure
    # Designed to fit into the following axis space:
    #    fig.add_axes([0.075,0.075,0.92,0.92],projection=ccrs.PlateCarree()) <- or some other projection type
    # INPUTS
    #   ob_lat: vector of observation latitudes
    #   ob_lon: vector of observation longitudes
    #   lat_rng: vector of latitude bin-edges
    #   lon_rng: vector of longitude bin-edges
    #   figax: figure axis (MUST include projection)
    # OUTPUTS
    #   figreturn: returned axis
    # DEPENDENCIES: matplotlib, numpy, cartopy
    #
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    # Compute total ob-count
    totobs=np.size(ob_lat)
    # Compute 2d histogram for upper-troposphere
    idx=np.where(ob_pre<50000.) # Pa
    uH,xe,ye=np.histogram2d(ob_lon[idx],ob_lat[idx],bins=(lon_rng,lat_rng))
    # Compute 2d histogram for lower-troposphere
    idx=np.where(ob_pre>=50000.) # Pa
    lH,xe,ye=np.histogram2d(ob_lon[idx],ob_lat[idx],bins=(lon_rng,lat_rng))
    # Compute bin centers
    xc=0.5*(xe[0:-1]+xe[1:])
    yc=0.5*(ye[0:-1]+ye[1:])
    # Define plot projection transform
    transform=figax.projection
    figreturn=figax
    # Generate plot
    #colmap=cm.get_cmap('gist_ncar').copy()
    colmap=cm.get_cmap('gist_ncar')
    colmap=truncate_colormap(colmap,0.15,0.35,n=256)
    lpfill=figax.pcolormesh(xc, yc, lH.T, transform=transform, cmap=colmap,alpha=0.67,vmin=0.05*np.max(uH+lH),vmax=np.max(uH+lH))
    lpfill.cmap.set_under('w')
    #colmap=cm.get_cmap('gist_ncar').copy()
    colmap=cm.get_cmap('gist_ncar')
    colmap=truncate_colormap(colmap,0.60,0.80,n=256)
    upfill=figax.pcolormesh(xc, yc, uH.T, transform=transform, cmap=colmap,alpha=0.67,vmin=0.05*np.max(uH+lH),vmax=np.max(uH+lH))
    upfill.cmap.set_under('w')
    pmap=figax.coastlines(resolution='50m',linewidth=2)
    # Add colorbar
    plt.colorbar(upfill,label='Upper Troposphere')
    plt.colorbar(lpfill,label='Lower Troposphere')
    # Add title
    figax.set_title('ob density ({:d} observations)'.format(totobs))
    # Return 
    return figreturn


def ob_hist_latlonpre(ob_lat,ob_lon,ob_pre,lat_rng,lon_rng,pre_rng,figax1,figax2,figax3):
    # Generates histograms of ob-count by latitude, longitude, and pressure.
    # The pressure-histogram is oriented along the y-axis for ease of plot
    # interpretation. Designed to fit the 3 plots into the following axis
    # spaces:
    #   (1) pressure-histogram: fig.add_axes([0.,0.,0.3,0.90])
    #   (2) latitude-histogram: fig.add_axes([0.4,0.,0.5,0.38])
    #   (3) longitude-histogram: fig.add_axes([0.4,0.52,0.5,0.38])
    #
    #   --------   ------------------
    #   |      |   |       3        |
    #   |      |   |                |
    #   |   1  |   ------------------
    #   |      |   |       2        |
    #   |      |   |                |
    #   --------   ------------------
    #
    # INPUTS
    #   ob_lat: vector of observation latitudes
    #   ob_lon: vector of observation longitudes
    #   ob_pre: vector of observation pressures
    #   lat_rng: vector of latitude bin-edges
    #   lon_rng: vector of longitude bin-edges
    #   pre_rng: vector of pressure bin-edges
    #   figax(1,2,3): figure axes for plots 1, 2, 3
    # OUTPUTS
    #   figreturn: returned axes
    # DEPENDENCIES: matplotlib, numpy
    #
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    # Generate pressure-histogram
    ax=figax1
    dy=pre_rng[1]-pre_rng[0]
    ax.hist(ob_pre,pre_rng,orientation="horizontal",facecolor='#0C00FF',edgecolor='w')
    ax.set_ylim((np.min(ob_pre)-dy,np.max(ob_pre)+dy))
    ax.invert_yaxis()
    ax.set_title('count by pressure')
    # Generate latitude-histogram
    ax=figax2
    dx=lat_rng[1]-lat_rng[0]
    ax.hist(ob_lat,lat_rng,facecolor='#E86D00',edgecolor='w')
    ax.set_xlim((np.min(ob_lat)-dx,np.max(ob_lat)+dx))
    ax.set_title('count by latitude')
    # Generate longitude-histogram
    ax=figax3
    ax.hist(ob_lon,lon_rng,facecolor='#D7D700',edgecolor='w')
    ax.set_xlim((np.min(ob_lon)-dx,np.max(ob_lon)+dx))
    ax.set_title('count by longitude')
    # Return figure axes
    return figax1, figax2, figax3


def ob_hist_spddirqi(ob_spd,ob_dir,ob_qi,spd_rng,dir_rng,qi_thresh,figax1,figax2,figax3):
    # Generates histograms of ob-count by wind speed and direction, and a pie-chart of obs >= or < qi_thresh
    # The direction-histogram is polar-oriented wth 0-deg facing south, as per wind convention
    # Designed to fit the 3 plots into the following axis
    # spaces:
    #    (1) windrose plot:    fig.add_axes([0.,0.,0.45,0.4],projection='polar')
    #    (2) speed histogram:  fig.add_axes([0.,0.52,0.9,0.33])
    #    (3) qi pi-chart:      fig.add_axes([0.5,0.,0.45,0.4])
    #
    #   -----------------------------
    #   |            2              |
    #   |                           |
    #   |----------------------------
    #   |     1      |      3       |
    #   |            |              |
    #   ----------------------------
    #
    # INPUTS
    #   ob_spd: vector of observation speeds
    #   ob_dir: vector of observation directions
    #   ob_qi: vector of observation quality-indicator values (typically QIFN or EE)
    #   spd_rng: vector of speed bin-edges
    #   dir_rng: vector of direction bin-edges
    #   qi_thresh: threshold of quality-indicator for good/bad obs
    #   figax(1,2,3): figure axes for plots 1, 2, 3
    # OUTPUTS
    #   figreturn: returned axes
    # DEPENDENCIES: matplotlib, numpy
    #
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    # NOTES:
    #       Sometimes QI is all np.nan values, in which case we will present a blank pie-chart
    #
    # Generate windrose (polar histogram)
    ax=figax1
    ax.set_theta_zero_location('S')
    ax.set_theta_direction(-1)
    h,x=np.histogram(ob_dir,dir_rng)
    dx=dir_rng[1]-dir_rng[0]
    xc=0.5*(x[0:-1]+x[1:])
    ax.bar(x=xc, height=h, width=0.75*dx*np.pi/180.,facecolor='#00B143',edgecolor='w')
    ax.set_title('wind direction')
    # Generate speed histogram
    ax=figax2
    ax.hist(ob_spd,spd_rng,facecolor='#CC00E8',edgecolor='w')
    dx=spd_rng[1]-spd_rng[0]
    ax.set_xlim((0.,np.max(ob_spd)+dx))
    ax.set_title('wind speed')
    # Generate pi-chart
    ax=figax3
    labels=['qi>={:.0f}'.format(qi_thresh),'qi<{:.0f}'.format(qi_thresh)]
    y=np.where(np.isnan(ob_qi)==False)
    if (np.size(y)>0):
        sizes=[np.size(np.where(ob_qi[y]>=qi_thresh)),np.size(np.where(ob_qi[y]<qi_thresh))]
        ax.pie(sizes, labels=labels, autopct='%1.1f%%',shadow=False, startangle=90,colors=['#00C5FF','#FF2D2D'])
        ax.axis('equal')
        ax.set_title('quality indicator')
    # Return
    return figax1,figax2,figax3


def stage_scorecard(ob_lat,ob_lon,ob_pre,ob_spd,ob_dir,ob_qi,qi_thresh=85.):
    # Stages sub-figures for score-card layout
    # INPUTS
    #   ob_lat: vector of ob latitudes
    #   ob_lon: vector of ob longitudes
    #   ob_pre: vector of ob pressures (Pa)
    #   ob_spd: vector of ob speeds
    #   ob_dir: vector of ob directions
    #   ob_qi: vector of ob quality-indicator values (usually QIFN, can also be EE)
    #   qi_threshold: threshold quality-indicator value for good/bad ob (often 85., as default)
    # OUTPUTS
    #   fighdl: figure handle containing plot
    # DEPENDENCIES: matplotlib, ob_density_plot, ob_hist_latlonpre, ob_hist_spddir
    #
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    # Outer figure domain
    figax=plt.figure(figsize=(21,14))
    # Split figure into a 2-col, 1-row set of subfigures
    # NOTE: subfigures is only available for matplotlib v.3.4.0 or later
    #subfigs = figax.subfigures(2, 1).flat
    # Top subfigure: ob_density_plot
    #sfig=subfigs[0]
    obDensityFig = plt.figure(figsize=(21,7))
    sfig=obDensityFig
    ax=sfig.add_axes([0.075,0.075,0.92,0.92],projection=ccrs.PlateCarree())
    lat_rng=np.arange(-90.,90.1,2.5)
    lon_rng=np.arange(0.,360.1,2.5)
    ax=ob_density_plot(ob_lat,ob_lon,ob_pre,lat_rng,lon_rng,figax=ax)
    # Bottom subfigure:
    obHistFig = plt.figure(figsize=(10.5,7))
    #sfig=subfigs[1]
    # Split bottom subfigure into a 1-row, 2-col set of sub-subfigures
    # NOTE: subfigures is only available for matplotlib v.3.4.0 or later
    #ssfigs=sfig.subfigures(1,2).flat
    # Left sub-subfigure: ob_hist_latlonpre
    obHistLatLonPreFig = plt.figure(figsize=(10.5,7))
    ssfig=obHistLatLonPreFig
    ax1=ssfig.add_axes([0.,0.,0.3,0.90])
    ax2=ssfig.add_axes([0.4,0.,0.5,0.38])
    ax3=ssfig.add_axes([0.4,0.52,0.5,0.38])
    lat_rng=np.arange(-90.,90.1,5.)
    lon_rng=np.arange(0.,360.1,10.)
    pre_rng=np.arange(10000.,110000.1,5000.)
    ax1,ax2,ax3=ob_hist_latlonpre(ob_lat,ob_lon,ob_pre,lat_rng,lon_rng,pre_rng,ax1,ax2,ax3)
    # Right sub-subfigure: ob_hist_spddirqi
    #ssfig=ssfigs[1]
    obHistSpdDirQIFig = plt.figure(figsize=(10.5,7))
    ssfig=obHistSpdDirQIFig
    ax1=ssfig.add_axes([0.,0.,0.45,0.4],projection='polar')
    ax2=ssfig.add_axes([0.,0.52,0.9,0.33])
    ax3=ssfig.add_axes([0.5,0.,0.45,0.4])
    spd_rng=np.arange(0.,100.1,2.)
    dir_rng=np.arange(0.,360.1,15.)
    ax1,ax2,ax3=ob_hist_spddirqi(ob_spd,ob_dir,ob_qi,spd_rng,dir_rng,qi_thresh,ax1,ax2,ax3)
    # Return figax
    # NOTE: return individual figures instead, if subfigures are not available
    #return figax
    return obDensityFig, obHistLatLonPreFig, obHistSpdDirQIFig
