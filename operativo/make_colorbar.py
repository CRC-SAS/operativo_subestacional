
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

from matplotlib import colors as c


#c_pp = ['#ffffff', '#bdc9e1', '#74a9cf', '#2b8cbe', '#045a8d']
#c_pp = ['#ffffff', '#fdae6b', '#fd8d3c', '#e6550d', '#a63603']
#c_pp = ['#ffffff', '#fdae6b', '#fd8d3c', '#e6550d', '#a63603']
#c_pp = ['#ffffff', '#d0d1e6', '#67a9cf', '#02818a', '#014636']
#cMap = c.ListedColormap(c_pp)
#bounds = np.array([0,20,40,60,80,100])
#norm = c.BoundaryNorm(boundaries=bounds, ncolors=len(c_pp))
#tick_l = ['0', '20', '40', '60', '80', '100']

#c_pp = ['#ffffff','#edf8b1','#c7e9b4','#7fcdbb','#41b6c4','#1d91c0','#225ea8','#253494','#081d58']
c_pp = ['#ffffff', '#ffeda0','#fed976','#feb24c','#fd8d3c','#fc4e2a','#e31a1c','#bd0026','#800026']
cMap = c.ListedColormap(c_pp)
bounds = np.array([0,20.01,30.01,40.01,50.01,60.01,70.01,80.01,90.01,100.01])
norm = c.BoundaryNorm(boundaries=bounds, ncolors=len(c_pp))
tick_l = ['0', '20', '30', '40', '50', '60', '70', '80', '90', '100']



fig = plt.figure()
ax = fig.add_axes([0.05, 0.80, 0.1, 0.9])

cb = mpl.colorbar.ColorbarBase(ax, orientation='vertical',
                               cmap=cMap,
                               norm=norm,  # vmax and vmin
                               ticks=bounds,
                               drawedges=True)
cb.ax.yaxis.set_ticks_position('left')
#cb.set_label(label=u'Precipitación (mm)', weight='bold')
cb.ax.set_title('Prob. (%)', weight='bold')
cb.ax.set_yticklabels(tick_l, weight='bold', fontsize=9)
plt.savefig('../figuras/colorbar2_vertical_new.jpg', bbox_inches='tight')
plt.close(fig)


###################
fig = plt.figure()
ax = fig.add_axes([0.05, 0.80, 0.9, 0.1])

cb = mpl.colorbar.ColorbarBase(ax, orientation='horizontal',
                               cmap=cMap,
                               norm=norm,  # vmax and vmin
                               ticks=bounds,
                               drawedges=True)
cb.ax.xaxis.set_ticks_position('bottom')
#cb.set_label(label=u'Precipitación (mm)', weight='bold')
cb.ax.set_title('Prob. (%)', weight='bold')
cb.ax.set_xticklabels(tick_l, weight='bold', fontsize=9)
plt.savefig('../figuras/colorbar2_horizontal_new.jpg', bbox_inches='tight')
plt.close(fig)
