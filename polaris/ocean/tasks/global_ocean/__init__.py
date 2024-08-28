from polaris import Step, Task
from polaris.config import PolarisConfigParser
from polaris.ocean.mesh.spherical import add_spherical_base_mesh_step
from polaris.ocean.resolution import resolution_to_subdir
from polaris.ocean.tasks.global_ocean.map import TopoMap


def add_global_ocean_tasks(component):
    """
    Add tasks that define variants of the global ocean test

    component : polaris.ocean.Ocean
        the ocean component that the tasks will be added to
    """
    filepath = 'spherical/icos/global_ocean/global_ocean.cfg'
    config = PolarisConfigParser(filepath=filepath)
    config.add_from_package('polaris.remap',
                            'mapping.cfg')
    config.add_from_package('polaris.ocean.tasks.global_ocean',
                            'global_ocean.cfg')
    component.add_task(GlobalOcean(component=component,
                                   config=config,
                                   icosahedral=True,
                                   include_viz=False,
                                   resolution=240.))
    component.add_task(GlobalOcean(component=component,
                                   config=config,
                                   icosahedral=True,
                                   include_viz=False))
    component.add_task(GlobalOcean(component=component,
                                   config=config,
                                   icosahedral=True,
                                   include_isc=True,
                                   include_viz=False,
                                   resolution=240.))
    component.add_task(GlobalOcean(component=component,
                                   config=config,
                                   icosahedral=True,
                                   include_isc=True,
                                   include_viz=False))


class GlobalOcean(Task):
    """
    Global ocean tests with realistic meshes

    Attributes
    ----------
    resolutions : list of float
        A list of mesh resolutions

    icosahedral : bool
        Whether to use icosahedral, as opposed to less regular, JIGSAW meshes

    include_viz : bool
        Include VizMap and Viz steps for each resolution
    """
    def __init__(self, component, config, icosahedral=True, include_isc=False,
                 include_viz=False, resolution=30.):
        """
        Create the convergence test

        Parameters
        ----------
        component : polaris.ocean.Ocean
            The ocean component that this task belongs to

        config : polaris.config.PolarisConfigParser
            A shared config parser

        icosahedral : bool
            Whether to use icosahedral, as opposed to less regular, JIGSAW
            meshes

        include_viz : bool
            Include VizMap and Viz steps for each resolution

        resolution: float, optional
            Resolution in km, only used for icos and qu
        """
        if icosahedral:
            prefix = 'icos'
        else:
            prefix = 'qu'

        mesh_name = resolution_to_subdir(resolution)
        taskdir = f'spherical/{prefix}/global_ocean/{mesh_name}'
        name = f'{prefix}_global_ocean_{mesh_name}'
        link = 'global_ocean.cfg'
        if include_isc:
            taskdir = f'{taskdir}/wISC'
            name = f'{name}_wISC'
        if include_viz:
            taskdir = f'{taskdir}/with_viz'
            name = f'{name}_with_viz'
        super().__init__(component=component, name=name, subdir=taskdir)
        self.resolution = resolution
        self.icosahedral = icosahedral
        self.include_isc = include_isc
        self.include_viz = include_viz

        self.set_shared_config(config, link=link)

        self._setup_steps()

    def configure(self):
        """
        Set config options for the test case
        """
        super().configure()

        # set up the steps again in case a user has provided new resolutions
        self._setup_steps()

    def _setup_steps(self):
        """ setup steps given resolutions """
        icosahedral = self.icosahedral
        resolution = self.resolution
        component = self.component

        # start fresh with no steps
        for step in list(self.steps.values()):
            self.remove_step(step)

        mesh_name = resolution_to_subdir(resolution)
        subdir = f'ocean/spherical/icos/{mesh_name}'
        base_mesh_step, mesh_name = add_spherical_base_mesh_step(
            component, resolution, icosahedral)
        self.add_step(base_mesh_step, symlink='base_mesh')

        subdir = f'{self.subdir}/topo/remap_base'
        topo_map_step = TopoMap(component=component,
                                name=f'topo_map_base_{mesh_name}',
                                subdir=subdir,
                                config=self.config,
                                mesh_name=mesh_name,
                                mesh_step=base_mesh_step,
                                mesh_filename='base_mesh.nc',
                                method='conserve',
                                smooth=False)
        self.add_step(topo_map_step)
