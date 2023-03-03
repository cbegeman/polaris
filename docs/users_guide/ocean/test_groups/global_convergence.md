(ocean-global-convergence)=

# global_convergence

The `global_convergence` test group implements convergence studies on the
full globe.  Three test cases from are included: the advection of a cosine bell,
and two nonlinear steady-state geostrophic flows.

(ocean-global-convergence-cosine-bell)=
(ocean-global-convergence-geostrophic)=
(ocean-global-convergence-geostrophic-wind)=


## cosine_bell

The `cosine_bell` test case implements the Cosine Bell test case as first
described in [Williamson et al. 1992](<https://doi.org/10.1016/S0021-9991(05)80016-6>)
but using the variant from Sec. 3a of
[Skamarock and Gassmann](https://doi.org/10.1175/MWR-D-10-05056.1).  A flow
field representing solid-body rotation transports a bell-shaped perturbation
in a tracer $psi$ once around the sphere, returning to its initial
location.  The bell is defined by:

$$
\psi =
    \begin{cases}
        \left( \psi_0/2 \right) \left[ 1 + \cos(\pi r/R )\right] &
            \text{if } r < R \\
        0 & \text{if } r \ge R
    \end{cases}
$$

where $\psi_0 = 1$, the bell radius $R = a/3$, and $a$ is
the radius of the sphere.  The equatorial velocity
$u_0 = 2 \pi a/ (\text{24 days})$. The time step is proportional to the
grid-cell size.

By default, the resolution is varied from 60 km to 240 km in steps of 30 km.
The result of the `analysis` step of the test case is a plot like the
following showing convergence as a function of the number of cells:

```{image} images/cosine_bell_convergence.png
:align: center
:width: 500 px
```

### config options

The `cosine_bell` config options include:

```cfg
# options for cosine bell convergence test case
[cosine_bell]

# the number of cells per core to aim for
goal_cells_per_core = 300

# the approximate maximum number of cells per core (the test will fail if too
# few cores are available)
max_cells_per_core = 3000

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
```

The last 7 options are used to control properties of the cosine bell and the
background properties.  The first 4 options are discussed below.

### resolutions

The default resolutions used in the test case depends on the mesh type. For
the `icos` mesh type, the defaults are:

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

### time step

The time step for forward integration is determined by multiplying the
resolution by `dt_per_km`, so that coarser meshes have longer time steps.
You can alter this before setup (in a user config file) or before running the
test case (in the config file in the work directory).

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

### initial state

The python code written by Darren Engwirda to set up this test case is a
useful starting place:
[SWE](<https://github.com/dengwirda/swe-python/blob/main/wtc.py>), especially
lines 58-132. 

The steady-state fields are given by the following equations:

$$
u = u_0 (cos\theta cos\alpha + cos\gamma sin\theta sin\alpha
v = -u_0 sin\gamma sin\alpha
h = h_0 - 1/g (a \Omega u_0 + u_0^2/2)(-cos\lambda cos\theta sin\alpha + sin\theta cos\alpha)^2
$$

where

$$
u_0 = 2 \pi a/(12 days)
h_0 = 2.94e-4/g
alpha = 0
$$

In this test case, the initial fields can be given their steady-state values
and the simulation should not diverge significantly from those values.
However, Williamson notes that the initial h field may be given a different
value to avoid spurious gravity waves.

In this test case, the bottom topography is flat so initial conditions are
given for `bottomDepth` and `ssh` such that $h = bottomDepth + ssh$.

The initial conditions must also include the coriolis parameter, given as:

$$
f = 2 \Omega (-cos\gamma cos\theta sin\alpha + sin\theta cos\alpha)
$$

In future work, alpha may be varied to test the sensitivity to orientation:

$$
\alpha = [0, 0.05, \pi/2 - 0.05, \pi/2]
$$

### forward

The model is run for 5 days. The time step should be adjusted in accordance
with the resolution.

### analysis

For analysis we compute the $l_1$, $l_2$ and $l_{\inf}$ error norms of h and
velocity relative to the steady-state solutions given above.

First, each of these errors norms are plotted vs time for a given resolution.

Then, mesh convergence is examined by plotting the $l_2$ and $l_{\inf}$ norms
at day 5 vs resolution.
