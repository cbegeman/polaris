import numpy as np
import xarray as xr
from mpas_tools.io import write_netcdf

from polaris import Step
from polaris.ocean.tasks.sphere_transport.resources.flow_types import (
    flow_divergent,
    flow_nondivergent,
    flow_rotation,
)
from polaris.ocean.tasks.sphere_transport.resources.tracer_distributions import (  # noqa: E501
    cosine_bells,
    slotted_cylinders,
)
from polaris.ocean.tasks.sphere_transport.resources.utils import (
    correlation_fn,
    xyztrig,
)
from polaris.ocean.vertical import init_vertical_coord


class Init(Step):
    """
    A step for an initial condition for for the cosine bell test case
    """
    def __init__(self, component, name, subdir, mesh_name, case_name):
        """
        Create the step

        Parameters
        ----------
        component : polaris.Component
            The component the step belongs to

        name : str
            The name of the step

        subdir : str
            The subdirectory for the step

        mesh_name : str
            The name of the mesh
        """
        super().__init__(component=component, name=name, subdir=subdir)

        self.case_name = case_name
        self.add_input_file(
            filename='mesh.nc',
            target=f'../../../base_mesh/{mesh_name}/base_mesh.nc')

        self.add_input_file(
            filename='graph.info',
            target=f'../../../base_mesh/{mesh_name}/graph.info')

        self.add_output_file(filename='initial_state.nc')

    def run(self):
        """
        Run this step of the task
        """
        config = self.config
        case_name = self.case_name

        section = config['sphere_transport']
        temperature = section.getfloat('temperature')
        salinity = section.getfloat('salinity')
        # lat_center = section.getfloat('lat_center')
        # lon_center = section.getfloat('lon_center')
        # radius = section.getfloat('radius')
        # psi0 = section.getfloat('psi0')
        # vel_pd = section.getfloat('vel_pd')

        section = config['vertical_grid']
        bottom_depth = section.getfloat('bottom_depth')

        ds_mesh = xr.open_dataset('mesh.nc')
        angleEdge = ds_mesh.angleEdge
        latCell = ds_mesh.latCell
        latEdge = ds_mesh.latEdge
        lonCell = ds_mesh.lonCell
        lonEdge = ds_mesh.lonEdge
        sphere_radius = ds_mesh.sphere_radius

        ds = ds_mesh.copy()

        ds['bottomDepth'] = bottom_depth * xr.ones_like(latCell)
        ds['ssh'] = xr.zeros_like(latCell)

        init_vertical_coord(config, ds)

        temperature_array = temperature * xr.ones_like(latCell)
        temperature_array, _ = xr.broadcast(temperature_array, ds.refZMid)
        ds['temperature'] = temperature_array.expand_dims(dim='Time', axis=0)
        ds['salinity'] = salinity * xr.ones_like(ds.temperature)

        tracer1 = xyztrig(lonCell, latCell)
        tracer2 = cosine_bells(lonCell, latCell)
        if case_name == 'correlated_tracers_2d':
            tracer3 = correlation_fn(tracer2)
        else:
            tracer3 = slotted_cylinders(lonCell, latCell)
        _, tracer1_array = np.meshgrid(ds.refZMid.values, tracer1)
        _, tracer2_array = np.meshgrid(ds.refZMid.values, tracer2)
        _, tracer3_array = np.meshgrid(ds.refZMid.values, tracer3)

        ds['tracer1'] = (('nCells', 'nVertLevels',), tracer1_array)
        ds['tracer1'] = ds.tracer1.expand_dims(dim='Time', axis=0)
        ds['tracer2'] = (('nCells', 'nVertLevels',), tracer2_array)
        ds['tracer2'] = ds.tracer2.expand_dims(dim='Time', axis=0)
        ds['tracer3'] = (('nCells', 'nVertLevels',), tracer3_array)
        ds['tracer3'] = ds.tracer3.expand_dims(dim='Time', axis=0)

        # Initialize velocity
        if case_name == 'rotation_2d':
            u, v = flow_rotation(lonEdge, latEdge)
        elif case_name == 'divergent_2d':
            u, v = flow_divergent(0., lonEdge, latEdge)
        elif (case_name == 'nondivergent_2d' or
              case_name == 'correlated_tracers_2d'):
            u, v = flow_nondivergent(0., lonEdge, latEdge)
        else:
            raise ValueError(f'Unexpected test case name {case_name}')
        normalVelocity = sphere_radius * (u * np.cos(angleEdge) +
                                          v * np.sin(angleEdge))
        normalVelocity, _ = xr.broadcast(normalVelocity, ds.refZMid)
        ds['normalVelocity'] = normalVelocity.expand_dims(dim='Time', axis=0)

        ds['fCell'] = xr.zeros_like(ds_mesh.xCell)
        ds['fEdge'] = xr.zeros_like(ds_mesh.xEdge)
        ds['fVertex'] = xr.zeros_like(ds_mesh.xVertex)

        write_netcdf(ds, 'initial_state.nc')


def cosine_bell(max_value, ri, r):
    return max_value / 2.0 * (1.0 + np.cos(np.pi * np.divide(ri, r)))
