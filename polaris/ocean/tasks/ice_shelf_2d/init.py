import numpy as np
import xarray as xr
from mpas_tools.cime.constants import constants
from mpas_tools.io import write_netcdf
from mpas_tools.mesh.conversion import convert, cull
from mpas_tools.planar_hex import make_planar_hex_mesh

from polaris import Step
from polaris.mesh.planar import compute_planar_hex_nx_ny
from polaris.ocean.vertical import init_vertical_coord


class Init(Step):
    """
    A step for creating a mesh and initial condition for ice shelf 2-d tasks

    Attributes
    ----------
    resolution : float
        The resolution of the task in km
    """
    def __init__(self, component, resolution, indir, thin_film=False,
                 time_varying_forcing=False):
        """
        Create the step

        Parameters
        ----------
        component : polaris.Component
            The component the step belongs to

        resolution : float
            The resolution of the task in km

        indir : str
            the directory the step is in, to which ``name`` will be appended
        """
        super().__init__(component=component, name='init', indir=indir)
        self.resolution = resolution
        self.thin_film = thin_film
        # TODO set up the time varying forcing in a separate step because the
        # rest of init is shared
        self.time_varying_forcing = time_varying_forcing

        self.add_output_file('output.nc',
                             validate_vars=['temperature', 'salinity',
                                            'layerThickness'])
        output_files = ['base_mesh.nc', 'culled_mesh.nc', 'culled_graph.info']
        if time_varying_forcing:
            output_files.append('land_ice_forcing.nc')
        for file in output_files:
            self.add_output_file(file)

    def run(self):
        """
        Run this step of the task
        """
        config = self.config
        logger = self.logger

        out_filename = self.outputs[0]
        print(out_filename)
        section = config['ice_shelf_2d']
        resolution = self.resolution

        # TODO change cfg options
        lx = section.getfloat('lx')
        ly = section.getfloat('ly')

        # these could be hard-coded as functions of specific supported
        # resolutions but it is preferable to make them algorithmic like here
        # for greater flexibility
        nx, ny = compute_planar_hex_nx_ny(lx, ly, resolution)
        dc = 1e3 * resolution

        ds_mesh = make_planar_hex_mesh(nx=nx, ny=ny, dc=dc,
                                       nonperiodic_x=False,
                                       nonperiodic_y=True)
        write_netcdf(ds_mesh, 'base_mesh.nc')

        ds_mesh = cull(ds_mesh, logger=logger)
        ds_mesh = convert(ds_mesh, graphInfoFileName='culled_graph.info',
                          logger=logger)
        write_netcdf(ds_mesh, 'culled_mesh.nc')

        ds = ds_mesh.copy()

        bottom_depth = config.getfloat('vertical_grid', 'bottom_depth')

        section = config['ice_shelf_2d']
        temperature = section.getfloat('temperature')
        surface_salinity = section.getfloat('surface_salinity')
        bottom_salinity = section.getfloat('bottom_salinity')
        coriolis_parameter = section.getfloat('coriolis_parameter')
        y1 = section.getfloat('y1') * 1e3
        y2 = section.getfloat('y2') * 1e3
        y3 = section.getfloat('y3') * 1e3

        # points 1 and 2 are where angles on ice shelf are located.
        # point 3 is at the surface.
        # d variables are total water-column thickness below ice shelf
        if self.thin_film:
            section = config['ice_shelf_2d_thin_film']
        else:
            section = config['ice_shelf_2d_default']
        d1 = section.getfloat('y1_water_column_thickness')
        d2 = section.getfloat('y2_water_column_thickness')
        d3 = bottom_depth
        print(d1)

        x_cell = ds.xCell
        y_cell = ds.yCell
        ds['bottomDepth'] = bottom_depth * xr.ones_like(ds.xCell)

        # Column thickness is a piecewise linear function
        column_thickness = xr.where(
            y_cell < y1,
            d1,
            d1 + (d2 - d1) * (y_cell - y1) / (y2 - y1))
        column_thickness = xr.where(
            y_cell < y2,
            column_thickness,
            d2 + (d3 - d2) * (y_cell - y2) / (y3 - y2))
        column_thickness = xr.where(
            y_cell < y3,
            column_thickness,
            d3)

        ds['ssh'] = -bottom_depth + column_thickness

        init_vertical_coord(config, ds)

        modify_mask = xr.where(y_cell < y3, 1, 0).expand_dims(
            dim='Time', axis=0)
        landIceFraction = modify_mask.astype(float)
        landIceMask = modify_mask.copy()
        landIceFloatingFraction = landIceFraction.copy()
        landIceFloatingMask = landIceMask.copy()

        ref_density = constants['SHR_CONST_RHOSW']
        landIceDraft = ds.ssh
        landIcePressure = _compute_land_ice_pressure_from_draft(
            land_ice_draft=landIceDraft, modify_mask=modify_mask,
            ref_density=ref_density)

        salinity = surface_salinity + ((bottom_salinity - surface_salinity) *
                                       (ds.zMid / (-bottom_depth)))
        salinity, _ = xr.broadcast(salinity, ds.layerThickness)
        ds['salinity'] = salinity.transpose('Time', 'nCells', 'nVertLevels')

        ds['temperature'] = temperature * xr.ones_like(ds.salinity)

        normal_velocity = xr.zeros_like(ds_mesh.xEdge)
        normal_velocity, _ = xr.broadcast(normal_velocity, ds.refBottomDepth)
        normal_velocity = normal_velocity.transpose('nEdges', 'nVertLevels')
        normal_velocity = normal_velocity.expand_dims(dim='Time', axis=0)

        ds['normalVelocity'] = normal_velocity
        ds['fCell'] = coriolis_parameter * xr.ones_like(x_cell)
        ds['fEdge'] = coriolis_parameter * xr.ones_like(ds_mesh.xEdge)
        ds['fVertex'] = coriolis_parameter * xr.ones_like(ds_mesh.xVertex)
        ds['modifyLandIcePressureMask'] = modify_mask
        ds['landIceFraction'] = landIceFraction
        ds['landIceFloatingFraction'] = landIceFloatingFraction
        ds['landIceMask'] = landIceMask
        ds['landIceFloatingMask'] = landIceFloatingMask
        ds['landIcePressure'] = landIcePressure
        ds['landIceDraft'] = landIceDraft

        ds.attrs['nx'] = nx
        ds.attrs['ny'] = ny
        ds.attrs['dc'] = dc

        if self.time_varying_forcing:
            _write_time_varying_forcing(
                config=config, ds_init=ds, section_name='ice_shelf_2d_forcing')

        write_netcdf(ds, out_filename)

        # Generate the tidal forcing dataset whether it is used or not
        ds_forcing = xr.Dataset()
        y_max = np.max(ds.yCell.values)
        ds_forcing['tidalInputMask'] = xr.where(
            y_cell > (y_max - 0.6 * dc), 1.0, 0.0)
        write_netcdf(ds_forcing, 'init_mode_forcing_data.nc')


def _compute_land_ice_pressure_from_draft(land_ice_draft, modify_mask,
                                          ref_density=None):
    """
    Compute the pressure from an overlying ice shelf from ice draft

    Parameters
    ----------
    land_ice_draft : xarray.DataArray
        The ice draft (sea surface height)

    modify_mask : xarray.DataArray
        A mask that is 1 where ``landIcePressure`` can be deviate from 0

    ref_density : float, optional
        A reference density for seawater displaced by the ice shelf

    Returns
    -------
    land_ice_pressure : xarray.DataArray
        The pressure from the overlying land ice on the ocean
    """
    gravity = constants['SHR_CONST_G']
    if ref_density is None:
        ref_density = constants['SHR_CONST_RHOSW']
    land_ice_pressure = \
        modify_mask * np.maximum(-ref_density * gravity * land_ice_draft, 0.)
    return land_ice_pressure


def _write_time_varying_forcing(config, ds_init, section_name):
    """
    Write time-varying land-ice forcing and update the initial condition
    """

    dates = config.get(section_name, 'dates')
    dates = [date.ljust(64) for date in dates.replace(',', ' ').split()]
    scales = config.get(section_name, 'scales')
    scales = [float(scale) for scale in scales.replace(',', ' ').split()]

    ds_out = xr.Dataset()
    ds_out['xtime'] = ('Time', dates)
    ds_out['xtime'] = ds_out.xtime.astype('S')

    landIceDraft = list()
    landIcePressure = list()
    landIceFraction = list()
    landIceFloatingFraction = list()

    for scale in scales:
        landIceDraft.append(scale * ds_init.landIceDraft)
        landIcePressure.append(scale * ds_init.landIcePressure)
        landIceFraction.append(ds_init.landIceFraction)
        landIceFloatingFraction.append(ds_init.landIceFloatingFraction)

    ds_out['landIceDraftForcing'] = xr.concat(landIceDraft, 'Time')
    ds_out.landIceDraftForcing.attrs['units'] = 'm'
    ds_out.landIceDraftForcing.attrs['long_name'] = \
        'The approximate elevation of the land ice-ocean interface'
    ds_out['landIcePressureForcing'] = \
        xr.concat(landIcePressure, 'Time')
    ds_out.landIcePressureForcing.attrs['units'] = 'm'
    ds_out.landIcePressureForcing.attrs['long_name'] = \
        'Pressure from the weight of land ice at the ice-ocean interface'
    ds_out['landIceFractionForcing'] = \
        xr.concat(landIceFraction, 'Time')
    ds_out.landIceFractionForcing.attrs['long_name'] = \
        'The fraction of each cell covered by land ice'
    ds_out['landIceFloatingFractionForcing'] = \
        xr.concat(landIceFloatingFraction, 'Time')
    ds_out.landIceFloatingFractionForcing.attrs['long_name'] = \
        'The fraction of each cell covered by floating land ice'
    write_netcdf(ds_out, 'land_ice_forcing.nc')

    ds_init['landIceDraft'] = scales[0] * ds_init.landIceDraft
    ds_init['ssh'] = ds_init.landIceDraft
    ds_init['landIcePressure'] = scales[0] * ds_init.landIcePressure
