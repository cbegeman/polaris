# Polaris

Polaris is a python package that provides an automated system to set up test 
cases or analysis tasks for several components of the Exascale Energy Earth 
System  Model ([E3SM](https://e3sm.org/).  The development version
of polaris will be kept closely synchronized with the development repositories
for the components it supports. Release versions will be compatible with 
specific tags of the MPAS components.

Many polaris test cases are idealized, and are used for things like
performing convergence tests or regression tests on particular parts of the
model code.  Many other polaris test cases, such as those under the
[global_ocean](ocean/global_ocean) and [greenland](landice/greenland) test 
groups, are "realistic" in the sense that they use data sets from observations 
to create  create global and regional meshes,  initial conditions, and boundary
conditions.

Polaris will be the tool used to create new land-ice and ocean meshes and
initial conditions for future versions of E3SM. 

```{note} Polaris does *not* provide the tools for creating many of the
files needed for full E3SM coupling, a process that requires expert help from
the E3SM development team.
```

The ``polaris`` python package defines the test cases and analysis tasks along 
with the commands  to list and set up both test cases and suites (groups 
of test cases or analysis tasks).  Polaris currently supports ``landice`` 
and ``ocean`` components.  Nearly all test cases include calls that launch one
of these E3SM components, built in "standalone" (uncoupled) mode.  These runs 
are configured with config files (e.g. YAML or namelist files) and one of the 
benefits of using polaris over attempting to run one of the components directly
is that polaris begins with default values for all these config options
for a given version of the component, modifying only those options where the 
default is not  appropriate. In this way, polaris requires little alteration 
as the model components themselves evolves and new functionality is added.

# Compass

The ``compass`` package is the predecessor of polaris. Documentation for 
compass can be found at:

<https://mpas-dev.github.io/compass/latest/>

the code can be found at:

<https://github.com/MPAS-Dev/compass/>
