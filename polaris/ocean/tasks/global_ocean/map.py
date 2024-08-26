from polaris.remap import MappingFileStep


class TopoMap(MappingFileStep):
    """
    A step for making a mapping file from a source topography file to the
    ISOMIP+ mesh

    Attributes
    ----------
    mesh_name : str
        The name of the mesh

    smooth : bool
        Whether to smooth the topography by inflating the destination cells
    """
    def __init__(self, component, name, subdir, config, mesh_name, mesh_step,
                 mesh_filename, method, smooth):
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

        config : polaris.config.PolarisConfigParser
            A shared config parser

        mesh_name : str
            The name of the mesh

        mesh_step : polaris.Step
            The base mesh step

        method : {'conserve', 'bilinear'}
            The remapping method to use

        smooth : bool
            Whether to smooth the topography by inflating the destination
            cells
        """
        super().__init__(component=component, name=name, subdir=subdir,
                         ntasks=128, min_tasks=1)
        if smooth and method != 'conserve':
            raise ValueError('Smoothing can only be used with the "conserve" '
                             'mapping method')
        self.mesh_name = mesh_name
        self.method = method
        self.smooth = smooth
        self.set_shared_config(config, link='global_ocean_topo.cfg')

        topo_filename = config.get('global_ocean_topography', 'topo_filename')
        self.add_input_file(
            filename='topography.nc',
            target=topo_filename,
            database='bathymetry_database')
        self.add_input_file(
            filename='base_mesh.nc',
            work_dir_target=f'{mesh_step.path}/{mesh_filename}')

    def runtime_setup(self):
        """
        Set up the source and destination grids for this step
        """

        config = self.config
        lon_var = config.get('global_ocean_topography', 'lon_var')
        lat_var = config.get('global_ocean_topography', 'lat_var')
        self.src_from_lon_lat(filename='topography.nc',
                              mesh_name='topography',
                              lon_var=lon_var,
                              lat_var=lat_var)
        self.dst_from_mpas(filename='base_mesh.nc', mesh_name=self.mesh_name)

        super().runtime_setup()
