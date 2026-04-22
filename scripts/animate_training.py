from pylab import *
import reciprocalspaceship as rs
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle
import seaborn as sns

# Define the range of checkpoints to animate
#100 checkpoints in one epoch for this example
stride=20
checkpoints = range(1, 301, stride)  # Adjust to your actual range
checkpoints_per_epoch = 1481 / 15

aspect = (16., 9.)
shrink = 1.8

f = plt.figure(figsize=np.array(aspect) / shrink)
#gs = mpl.gridspec.GridSpec(1, 3)
#ax1 = f.add_subplot(gs[:,0])
#ax2 = f.add_subplot(gs[:,1])
#ax3 = f.add_subplot(gs[:,2])

gs = mpl.gridspec.GridSpec(20, 20)
ax1 = f.add_subplot(gs[:5,1:10])
ax2 = f.add_subplot(gs[6:,:10])
ax3 = f.add_subplot(gs[6:,10:])
ax4 = f.add_subplot(gs[1:3,11:19])
ax5 = f.add_subplot(gs[3:6,10:19])

# Set up ax1 properties once
#ax1.loglog()
ax1.tick_params(which='both', left=False, bottom=False, labelleft=False, labelbottom=False)
ax1.set_xticks([])
ax2.set_yticks([0., 1.])

# Set up ax2 and ax3 properties once
ax2.set_xticks([])
ax2.set_yticks([])
ax3.set_xticks([])
ax3.set_yticks([])

# Create progress bar element (will be updated each frame)
progress_bar = None
progress_text = None

def plot_fit(checkpoint, ax, bins=20, method='pearson'):
    # Plot new data
    #ds = rs.read_mtz(f"asu_0_epoch_{checkpoint}.mtz").stack_anomalous()
    ds = rs.read_mtz(f"asu_0_epoch_{checkpoint}.mtz").join(
        rs.read_mtz(f"eff_0_asu_0_epoch_{checkpoint}/refine_001.mtz"), check_isomorphous=False
    ).stack_anomalous()
    ds,labels = ds.assign_resolution_bins(bins)
    k1,k2 = 'F-obs-filtered', 'F-model'
    ds['Set'] = np.array(['Working', 'Free'])[ds['R-free-flags']]
    cc = ds[['bin', 'Set', k1, k2]].groupby(['bin', 'Set']).corr(method).loc[:,:,k1][[k2]]
    cc = cc.reset_index()
    ax.plot(np.arange(bins), cc[cc.Set == 'Working'][k2], '-k', label='Working')
    ax.plot(np.arange(bins), cc[cc.Set == 'Free'][k2], '--k', label='Free')
    ax.plot(ax.get_xlim(), [1., 1.], '--r', label='Corr.=1', scalex=False, scaley=False)
    ax.set_xlabel("Resolution")
    ax.set_ylabel("Corr. to\nStructure")
    #ax.legend(loc='lower left')
    ax.set_ylim([-0.1, 1.05])
    h, l = ax.get_legend_handles_labels() # get labels and handles from ax1
    ax5.axis('off')
    ax5.legend(h, l, loc='lower left', ncol=3, labelspacing=0.1)

def update(checkpoint):
    global progress_bar, progress_text
    
    # Clear the axes
    ax1.clear()
    ax2.clear()
    ax3.clear()
    
    # Reapply ax1 settings after clearing
    plot_fit(checkpoint, ax1)
    #ax1.tick_params(which='both', left=False, bottom=False, labelleft=False, labelbottom=False)
    
    im = imread(f"eff_0_asu_0_epoch_{checkpoint}/zn.png")
    ax2.imshow(im)
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_xlabel("Zinc Anomalous")

    im = imread(f"eff_0_asu_0_epoch_{checkpoint}/met_120.png")
    ax3.imshow(im)
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax3.set_xlabel("Methionine Alternate Conf")

    # Calculate epoch
    epoch = checkpoint / checkpoints_per_epoch
    max_epoch = max(checkpoints) / checkpoints_per_epoch

    # Add progress bar
    # Position: left, bottom, width, height (in figure coordinates)
    bar_height = 0.02
    bar_bottom = 0.90
    bar_left = 0.6
    bar_width = 0.3
    
    # Remove old progress bar if it exists
    if progress_bar is not None:
        progress_bar.remove()
    if progress_text is not None:
        progress_text.remove()
    
    # Background bar (gray)
    #ax_prog = f.add_axes([bar_left, bar_bottom, bar_width, bar_height])
    ax_prog = ax4
    ax_prog.set_xlim(0, max_epoch)
    ax_prog.set_ylim(0, 1)
    ax_prog.axis('off')
    
    # Background
    ax_prog.add_patch(Rectangle((0, 0), max_epoch, 1, 
                                facecolor='grey', edgecolor='black', linewidth=1))
    
    # Progress (filled portion)
    progress_bar = ax_prog.add_patch(Rectangle((0, 0), epoch, 1, 
                                                facecolor='black', edgecolor='black', linewidth=1))
    
    # Text label
    progress_text = ax_prog.text(max_epoch / 2, 0.5, f'Epoch: {epoch:.2f} / {max_epoch:.0f}', 
                                 ha='center', va='center', fontsize=10, fontweight='bold', color='w')

    plt.tight_layout()

update(1)

# Create animation
ani = FuncAnimation(f, update, frames=checkpoints, interval=20, repeat=True)

# To save the animation (optional)
ani.save('animation.mp4', writer='ffmpeg', fps=5)
# ani.save('animation.gif', writer='pillow', fps=5)

# To display the animation
#plt.show()
