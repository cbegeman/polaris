from polaris.ocean.model import OceanModelStep


class Forward(OceanModelStep):
    """
    A step for performing forward ocean component runs as part of single_column
    test cases.

    Attributes
    ----------
    resources_fixed : bool
        Whether resources were set already and shouldn't be updated
        algorithmically
    """

    def __init__(
        self,
        component,
        name='forward',
        subdir=None,
        indir=None,
        ntasks=None,
        min_tasks=None,
        openmp_threads=1,
        validate_vars=None,
        task_name='',
    ):
        """
        Create a new test case

        Parameters
        ----------
        component : polaris.Component
            The component the step belongs to

        name : str
            the name of the step

        subdir : str, optional
            the subdirectory for the step.  If neither this nor ``indir``
             are provided, the directory is the ``name``

        indir : str, optional
            the directory the step is in, to which ``name`` will be appended

        ntasks : int, optional
            the number of tasks the step would ideally use.  If fewer tasks
            are available on the system, the step will run on all available
            tasks as long as this is not below ``min_tasks``

        min_tasks : int, optional
            the number of tasks the step requires.  If the system has fewer
            than this number of tasks, the step will fail

        openmp_threads : int, optional
            the number of OpenMP threads the step will use

        validate_vars : list, optional
            A list of variable names to compare with a baseline (if one is
            provided)

        task_name : str, optional
            the name of the test case
        """
        super().__init__(
            component=component,
            name=name,
            subdir=subdir,
            indir=indir,
            ntasks=ntasks,
            min_tasks=min_tasks,
            openmp_threads=openmp_threads,
        )

        self.add_yaml_file('polaris.ocean.config', 'output.yaml')

        self.add_input_file(
            filename='initial_state.nc', target='../init/initial_state.nc'
        )
        self.add_input_file(filename='forcing.nc', target='../init/forcing.nc')
        self.add_input_file(
            filename='graph.info', target='../init/culled_graph.info'
        )

        self.package = 'polaris.tasks.ocean.single_column'
        self.yaml_filename = 'forward.yaml'
        self.task_name = task_name

        self.add_output_file(filename='output.nc', validate_vars=validate_vars)

        self.resources_fixed = ntasks is not None

    def dynamic_model_config(self, at_setup):
        config = self.config
        model = config.get('ocean', 'model')
        vert_levels = config.get('vertical_grid', 'vert_levels')
        if model == 'mpas-ocean' and vert_levels == 1:
            self.add_yaml_file('polaris.ocean.config', 'single_layer.yaml')
        time_integrator = config.get('single_column_inertial','time_integrator')
        time_integrator_map = dict([('RK4', 'RungeKutta4')])
        model = config.get('ocean', 'model')
        if model == 'omega':
            if time_integrator in time_integrator_map.keys():
                time_integrator = time_integrator_map[time_integrator]
            else:
                print(
                    'Warning: mapping from time integrator '
                    f'{time_integrator} to omega not found, '
                    'retaining name given in config'
                )
        if self.task_name == 'ekman':
            nu = self.config.getfloat(
                'single_column_ekman', 'vertical_viscosity'
            )
            self.add_model_config_options(
                options={'config_cvmix_background_viscosity': nu},
                config_model='mpas-ocean',
            )
        replacements = dict(
            time_integrator=time_integrator,
        )

        self.add_yaml_file(
            self.package,
            self.yaml_filename,
            template_replacements=replacements,
        )
        self.add_yaml_file(
            f'{self.package}.{self.task_name}', self.yaml_filename
        )
