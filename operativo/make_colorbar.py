
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colorbar
import numpy as np

from matplotlib import colors as c


c_pp = ['#ffffff', '#ffeda0','#fed976','#feb24c','#fd8d3c','#fc4e2a','#e31a1c','#bd0026','#800026']
c_map = c.ListedColormap(c_pp)
bounds = np.array([0, 20.01, 30.01, 40.01, 50.01, 60.01, 70.01, 80.01, 90.01, 100.01])
norm = c.BoundaryNorm(boundaries=bounds, ncolors=len(c_pp))
tick_l = ['0', '20', '30', '40', '50', '60', '70', '80', '90', '100']


###################
fig = plt.figure()
ax = fig.add_axes((0.05, 0.80, 0.1, 0.9))

cb = mpl.colorbar.ColorbarBase(ax, orientation='vertical',
                               cmap=c_map,
                               norm=norm,
                               ticks=bounds,
                               drawedges=True)

cb.ax.yaxis.set_ticks_position('left')
cb.ax.set_title('Prob. (%)', weight='bold')
cb.ax.set_yticklabels(tick_l, weight='bold', fontsize=9)
plt.savefig('../figuras/colorbar2_vertical_new.jpg', bbox_inches='tight')
plt.close(fig)


###################
fig = plt.figure()
ax = fig.add_axes((0.05, 0.80, 0.9, 0.1))

cb = mpl.colorbar.ColorbarBase(ax, orientation='horizontal',
                               cmap=c_map,
                               norm=norm,
                               ticks=bounds,
                               drawedges=True)

cb.ax.xaxis.set_ticks_position('bottom')
cb.ax.set_title('Prob. (%)', weight='bold')
cb.ax.set_xticklabels(tick_l, weight='bold', fontsize=9)
plt.savefig('../figuras/colorbar2_horizontal_new.jpg', bbox_inches='tight')
plt.close(fig)
