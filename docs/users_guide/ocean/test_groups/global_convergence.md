(ocean-global-convergence)=

# global_convergence

The `global_convergence` test group implements convergence studies on the
full globe.  Three test cases from are included: the advection of a cosine bell,
and two nonlinear steady-state geostrophic flows.

(ocean-global-convergence-cosine-bell)=
(ocean-global-convergence-geostrophic)=
(ocean-global-convergence-geostrophic-wind)=


## cosine_bell

### Description

The `cosine_bell` test case implements the Cosine Bell test case as first
described in [Williamson et al. 1992](<https://doi.org/10.1016/S0021-9991(05)80016-6>)
but using the variant from Sec. 3a of
[Skamarock and Gassmann](https://doi.org/10.1175/MWR-D-10-05056.1).  A flow
field representing solid-body rotation transports a bell-shaped perturbation
in a tracer $psi$ once around the sphere, returning to its initial
location.

The test is a convergence test with time step varying proportionately to grid
size. The result of the `analysis` step of the test case is a plot like the
following showing convergence as a function of the number of cells:

```{image} images/cosine_bell_convergence.png
:align: center
:width: 500 px
```

### mesh

Two global mesh variants are tested, quasi-uniform (QU) and icosohydral. The
default resolutions used in the test case depends on the mesh type.

For the `icos` mesh type, the defaults are:

```cfg
resolutions = 60, 120, 240, 480
```

for the `qu` mesh type, they are:

```cfg
resolutions = 60, 90, 120, 150, 180, 210, 240
```

To alter the resolutions used in this test, you will need to create your own
config file (or add a `cosine_bell` section to a config file if you're
already using one).  The resolutions are a comma-separated list of the
resolution of the mesh in km.  If you specify a different list
before setting up `cosine_bell`, steps will be generated with the requested
resolutions.  (If you alter `resolutions` in the test case's config file in
the work directory, nothing will happen.)  For `icos` meshes, make sure you
use a resolution close to those listed in {ref}`dev-spherical-meshes`.  Each
resolution will be rounded to the nearest allowed icosahedral resolution.

### vertical grid

This test case only exercises the shallow water dynamics. As such, the minimum
number of vertical levels may be used. The bottom depth is constant and the
results should be insensitive to the choice of `bottom_depth`.

```cfg
# Options related to the vertical grid
[vertical_grid]

# the type of vertical grid
grid_type = uniform

# Number of vertical levels
vert_levels = 3

# Depth of the bottom of the ocean
bottom_depth = 300.0

# The type of vertical coordinate (e.g. z-level, z-star)
coord_type = z-level

# Whether to use "partial" or "full", or "None" to not alter the topography
partial_cell_type = None

# The minimum fraction of a layer for partial cells
min_pc_fraction = 0.1
```

### initial conditions

The initial bell is defined by any passive tracer $\psi$:

$$
\psi =
    \begin{cases}
        \left( \psi_0/2 \right) \left[ 1 + \cos(\pi r/R )\right] &
            \text{if } r < R \\
        0 & \text{if } r \ge R
    \end{cases}
$$

where $\psi_0 = 1$, the bell radius $R = a/3$, and $a$ is the radius of the
sphere. `psi_0` and `radius`, $R$, are given as config options and may be
altered by the user. In the `initial_state step` we assign `debug_tracers_1`
to $\psi$.

The initial velocity is equatorial:

$$
u_0 = 2 \pi a/ \tau
$$

Where $\tau$ is the time it takes to transit the equator. The default is 24
days, and can be altered by the user using the config option `vel_pd`.

Temperature and salinity are not evolved in this test case and are given
constant values determined by config options `temperature` and `salinity`.

The Coriolis parameters `fCell`, `fEdge`, and `fVertex` do not need to be
specified for a global mesh and are initialized as zeros.

### forcing

N/A. This case is run with all velocity tendencies disabled so the velocity
field remains at the initial velocity $u_0$.

### time step and run duration

The time step for forward integration is determined by multiplying the
resolution by `dt_per_km`, so that coarser meshes have longer time steps.
You can alter this before setup (in a user config file) or before running the
test case (in the config file in the work directory). The run duration is 24
days.

### config options

The `cosine_bell` config options include:

```cfg
# options for cosine bell convergence test case
[cosine_bell]

# time step per resolution (s/km), since dt is proportional to resolution
dt_per_km = 30

# the constant temperature of the domain
temperature = 15.0

# the constant salinity of the domain
salinity = 35.0

# the central latitude (rad) of the cosine bell
lat_center = 0.0

# the central longitude (rad) of the cosine bell
lon_center = 3.14159265

# the radius (m) of cosine bell
radius = 2123666.6667

# hill max of tracer
psi0 = 1.0

# time (days) for bell to transit equator once
vel_pd = 24.0

# convergence threshold below which the test fails for QU meshes
qu_conv_thresh = 1.8

# Convergence rate above which a warning is issued for QU meshes
qu_conv_max = 2.2

# convergence threshold below which the test fails for icosahedral meshes
icos_conv_thresh = 1.8

# Convergence rate above which a warning is issued for icosahedral meshes
icos_conv_max = 2.2


# options for visualization for the cosine bell convergence test case
[cosine_bell_viz]

# visualization latitude and longitude resolution
dlon = 0.5
dlat = 0.5

# remapping method ('bilinear', 'neareststod', 'conserve')
remap_method = conserve

# colormap options
# colormap
colormap_name = viridis

# the type of norm used in the colormap
norm_type = linear

# A dictionary with keywords for the norm
norm_args = {'vmin': 0., 'vmax': 1.}

# We could provide colorbar tick marks but we'll leave the defaults
# colorbar_ticks = np.linspace(0., 1., 9)
```

The `dt_per_km` option `[cosine_bell]` is used to control the time step, as
discussed above in more detail.

The 7 options from `temperature` to `vel_pd` are used to control properties of
the cosine bell and the rest of the sphere, as well as the advection.

The options `qu_conv_thresh` to `icos_conv_max` are thresholds for determining
when the convergence rates are not within the expected range.

The options in the `cosine_bell_viz` section are used in visualizing the
initial and final states on a lon-lat grid.

### cores

The number of cores (and the minimum) is proportional to the number of cells,
so that the number of cells per core is roughly constant.  You can alter how
many cells are allocated to each core with `goal_cells_per_core`.  You can
control the maximum number of cells that are allowed to be placed on a single
core (before the test case will fail) with `max_cells_per_core`.  If there
aren't enough processors to handle the finest resolution, you will see that
the step (and therefore the test case) has failed.

## geostrophic

The `geostrophic` test case implements the "Global Steady State Nonlinear
Zonal Geostrophic Flow" test case described in
[Williamson et al. 1992](<https://doi.org/10.1016/S0021-9991(05)80016-6>)

### mesh

The mesh is global and can be constructed either as quasi-uniform or
icosahedral. At least three resolutions must be chosen for the mesh
convergence study. The test group may be defined such that the mesh steps from
the `cosine_bell` case are used for this test case.

### vertical grid

This test case only exercises the shallow water dynamics. As such, the minimum
number of vertical levels may be used. The bottom depth is constant and the
results should be insensitive to the choice of `bottom_depth`. The `cosine_bell`
options may be used.

### initial conditions

The python code written by Darren Engwirda to set up this test case is a
useful starting place:
[SWE](<https://github.com/dengwirda/swe-python/blob/main/wtc.py>), especially
lines 58-132. 

The steady-state fields are given by the following equations:

$$
u & = u_0 (\cos\theta \cos\alpha + \cos\gamma \sin\theta \sin\alpha\\
v & = -u_0 \sin\gamma \sin\alpha\\
h & = h_0 - 1/g (a \Omega u_0 + u_0^2/2)(-\cos\lambda \cos\theta \sin\alpha + \sin\theta \cos\alpha)^2
$$

where

$$
u_0 & = 2 \pi a/(12 \textrm{ days})\\
h_0 & = 2.94e-4/g \\
\alpha & = 0
$$

In this test case, the initial fields can be given their steady-state values
and the simulation should not diverge significantly from those values.
However, Williamson notes that the initial h field may be given a different
value to avoid spurious gravity waves.

In this test case, the bottom topography is flat so initial conditions are
given for `bottomDepth` and `ssh` such that `h = bottomDepth + ssh`.

The initial conditions must also include the coriolis parameter, given as:

$$
f = 2 \Omega (-\cos\gamma \cos\theta \sin\alpha + \sin\theta \cos\alpha)
$$

In future work, alpha may be varied to test the sensitivity to orientation:

$$
\alpha = [0, 0.05, \pi/2 - 0.05, \pi/2]
$$

### forcing

Probably N/A but see Williamson's text about the possibility of prescribing a wind field.

### time step and run duration

The model is run for 5 days. The time step should be adjusted in accordance
with the resolution.

### analysis

For analysis we compute the $l_1$, $l_2$ and $l_{\inf}$ error norms of h and
velocity relative to the steady-state solutions given above.

First, each of these errors norms are plotted vs time for a given resolution.

Then, mesh convergence is examined by plotting the $l_2$ and $l_{\inf}$ norms
at day 5 vs resolution.

### config options

TBD

### cores

See `cosine_bell` description.
