from polaris import Step, Task
from polaris.config import PolarisConfigParser
from polaris.ocean.mesh.spherical import add_spherical_base_mesh_step


def add_global_ocean_tasks(component):
    """
    Add tasks that define variants of the global ocean test

    component : polaris.ocean.Ocean
        the ocean component that the tasks will be added to
    """
    filepath = 'spherical/icos/global_ocean/global_ocean.cfg'
    config = PolarisConfigParser(filepath=filepath)
    config.add_from_package('polaris.ocean.tasks.global_ocean',
                            'global_ocean.cfg')
    component.add_task(GlobalOcean(component=component,
                                   config=config,
                                   icosahedral=True,
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
    def __init__(self, component, config, icosahedral, include_viz,
                 resolution=30.):
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

        subdir = f'spherical/{prefix}/global_ocean'
        name = f'{prefix}_global_ocean'
        if include_viz:
            subdir = f'{subdir}/with_viz'
            name = f'{name}_with_viz'
            link = 'global_ocean.cfg'
        else:
            # config options live in the task already so no need for a symlink
            link = None
        super().__init__(component=component, name=name, subdir=subdir)
        self.resolution = resolution
        self.icosahedral = icosahedral
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
        if icosahedral:
            prefix = 'icos'
        else:
            prefix = 'qu'

        subdir = f'ocean/spherical/icos/{int(resolution)}km'
        if subdir in component.steps:
            base_mesh_step = component.steps[subdir]
            mesh_name = f'{prefix}_{int(resolution)}km'
        else:
            base_mesh_step, mesh_name = add_spherical_base_mesh_step(
                component, resolution, icosahedral)
        self.add_step(base_mesh_step, symlink=f'base_mesh/{mesh_name}')
