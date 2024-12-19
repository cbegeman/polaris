import cmocean  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from polaris import Step
from polaris.viz import use_mplstyle


class Viz(Step):
    """
    A step for plotting the results of a single-column test
    """
    def __init__(self, component, indir, ideal_age=False):
        """
        Create the step

        Parameters
        ----------
        component : polaris.Component
            The component the step belongs to

        indir : str
            The subdirectory that the task belongs to, that this step will
            go into a subdirectory of

        ideal_age : bool, optional
            Whether the initial condition should include the ideal age tracer
        """
        super().__init__(component=component, name='viz', indir=indir)
        self.ideal_age = ideal_age
        self.add_input_file(
            filename='initial_state.nc',
            target='../init/initial_state.nc')
        self.add_input_file(
            filename='output.nc',
            target='../forward/output.nc')
        self.add_input_file(
            filename='conservationCheck.nc',
            target='../forward/conservationCheck.nc')
        self.add_input_file(
            filename='KPP.nc',
            target='../forward/KPP.nc')

    def run(self):
        """
        Run this step of the test case
        """
        use_mplstyle()
        ideal_age = self.ideal_age

        ds = xr.load_dataset('output.nc')
        ds_kpp = xr.load_dataset('KPP.nc')
        t_index = ds.sizes['Time'] - 1
        t = ds.daysSinceStartOfSim[t_index]
        ns_per_day = 3600. * 24. * 1.e9
        time = ds['daysSinceStartOfSim']
        time_days = time.values.astype("float64") / ns_per_day
        az1 = -18.48
        ds['freezingTemperature'] = \
            (1. / az1) * ds.salinity / (1. - ds.salinity * 1.0e-3)
        ds['thermalForcing'] = ds.temperature - ds.freezingTemperature
        ds['vertDiffTopOfCell'] = ds_kpp.vertDiffTopOfCell
        if 'frazilSalinityTendency' in ds.keys():
            ds['frazilSalinityTendencyCorrected'] = \
                (ds.frazilSalinityTendency -
                 ds.salinity * ds.frazilLayerThicknessTendency) / \
                ds.layerThickness
        ds['RiTopOfCell'] = ds_kpp.RiTopOfCell
        fields = {'temperature': r'$^{\circ}$C',
                  'thermalForcing': r'$^{\circ}$C',
                  'vertVelocityTop': 'm s$^{-1}$',
                  'salinity': 'PSU',
                  'vertVelocityTop': r'm s$^{-1}$',
                  'frazilLayerThicknessTendency': r'm s$^{-1}$',
                  'frazilTemperatureTendency': r'$^{\circ}$C s$^{-1}$',
                  'salinityVerticalAdvectionTendency': r'PSU s$^{-1}$',
                  'salinityVertMixTendency': r'PSU s$^{-1}$',
                  'RiTopOfCell': '',
                  'frazilSalinityTendencyCorrected': r'PSU s$^{-1}$',
                  'frazilSalinityTendency': r'PSU m s$^{-1}$'}
        options = {'temperature': 'cmo.thermal',
                   'thermalForcing': 'cmo.balance',
                   'salinity': 'cmo.haline',
                   'vertVelocityTop': 'cmo.balance',
                   'salinityVerticalAdvectionTendency': 'cmo.balance',
                   'salinityVertMixTendency': 'cmo.balance',
                   'frazilLayerThicknessTendency': 'cmo.balance',
                   'RiTopOfCell': 'cmo.balance',
                   'frazilTemperatureTendency': 'cmo.balance',
                   'frazilSalinityTendencyCorrected': 'cmo.balance',
                   'frazilSalinityTendency': 'cmo.balance'}
        if ideal_age:
            fields['iAge'] = 'seconds'
        z_mid = ds['zMid'].mean(dim='nCells')
        z_top = ds['zTop'].mean(dim='nCells')
        z_bed = np.ones((ds.sizes['Time'], 1)) * \
            ds.bottomDepth.mean(dim='nCells').values
        z = np.concat([z_top.values, -z_bed], axis=1)
        zmesh = np.concat([z, z[-1:, :]], axis=0)
        end_time = [time_days[-1] + time_days[1],]
        t = np.concat([time_days, end_time])
        _, tmesh = np.meshgrid(z[0, :], t)
        for field_name, field_units in fields.items():
            if field_name not in ds.keys():
                print(f'{field_name} not present in output.nc')
                continue
            var = ds[field_name].mean(dim='nCells')
            if 'nVertLevelsP1' in var.dims:
                var = var.values[:, 1:]
            plt.figure(figsize=(5, 3))
            ax = plt.subplot(111)
            cmap = options[field_name]
            if cmap == 'cmo.balance':
                vmax = np.max(np.abs(var[1:, :]))
                vmin = -vmax
            else:
                vmin = np.min(var[1:, :])
                vmax = np.max(var[1:, :])
            p = ax.pcolormesh(tmesh[1:, :], -zmesh[1:, :], var[1:, :],
                              cmap=cmap, vmin=vmin, vmax=vmax)
            ax.invert_yaxis()
            ax.set_yscale('linear')
            cbar = plt.colorbar(p)
            cbar.ax.set_title(f'{field_name} ({field_units})')
            ax.set_xlabel('Time (days)')
            ax.set_ylabel('z (m)')
            plt.tight_layout(pad=0.5)
            plt.savefig(f'{field_name}.png', dpi=200)
            plt.close()

        fields = {'temperatureTend': r'C s$^{-1}$',
                  'temperatureVerticalAdvectionTendency': r'C s$^{-1}$',
                  'temperatureVertMixTendency': r'C s$^{-1}$',
                  'frazilTemperatureTendency': r'C s$^{-1}$'}
        plt.figure(figsize=(12, 3))
        ax = plt.subplot(111)
        z_mid_final = z_mid.isel(Time=t_index)
        for field_name, field_units in fields.items():
            if field_name not in ds.keys():
                print(f'{field_name} not present in output.nc')
                continue
            var = ds[field_name].mean(dim='nCells')
            var_final = var.isel(Time=t_index)
            ax.plot(var_final, -z_mid_final, label=field_name)
            ax.plot([0, 0],
                    [np.min(-z_mid_final), np.max(-z_mid_final)],
                    '--k', label=None)
        ax.set_yscale('log')
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set_xlabel(f'Temperature tendency ({field_units})')
        ax.set_ylim([min(-z_mid_final), 50])
        ax.invert_yaxis()
        ax.set_ylabel('z (m)')
        plt.tight_layout(pad=0.5)
        plt.savefig('temperature_tendency.png', dpi=200)
        plt.close()

        fields = {'salinityTend': r'PSU s$^{-1}$',
                  'salinityVerticalAdvectionTendency': r'PSU s$^{-1}$',
                  'salinityVertMixTendency': r'PSU s$^{-1}$',
                  'frazilSalinityTendency': r'PSU s$^{-1}$'}
        plt.figure(figsize=(12, 3))
        ax = plt.subplot(111)
        z_mid_final = z_mid.isel(Time=t_index)
        for field_name, field_units in fields.items():
            if field_name not in ds.keys():
                print(f'{field_name} not present in output.nc')
                continue
            var = ds[field_name].mean(dim='nCells')
            var_final = var.isel(Time=t_index)
            ax.plot(var_final, -z_mid_final, label=field_name)
            ax.plot([0, 0],
                    [np.min(-z_mid_final), np.max(-z_mid_final)],
                    '--k', label=None)
        ax.set_yscale('log')
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set_xlabel(f'Salinity tendency ({field_units})')
        ax.set_ylim([np.min(-z_mid_final), 50])
        ax.set_ylabel('z (m)')
        ax.invert_yaxis()
        plt.tight_layout(pad=0.5)
        plt.savefig('salinity_tendency.png', dpi=200)
        plt.close()

        rho_ice = 1000.  # config_frazil_ice_density
        if 'accumulatedFrazilIceMass' in ds.keys():
            ds['frazilIceThickness'] = ds.accumulatedFrazilIceMass / rho_ice
        if 'accumulatedFrazilIceSalinity' in ds.keys():
            ds['frazilIceSalt'] = ds.accumulatedFrazilIceSalinity * \
                ds.accumulatedFrazilIceMass
        fields = {'frazilSurfacePressure': 'Pa',
                  'ssh': 'm',
                  'frazilIceThickness': 'm',
                  'frazilIceSalt': 'g',
                  'accumulatedFrazilIceMass': 'kg m^2',
                  'accumulatedFrazilIceSalinity': 'g kg$^{-1}$'}
        for field_name, field_units in fields.items():
            if field_name not in ds.keys():
                print(f'{field_name} not present in output.nc')
                continue
            var = ds[field_name]
            if 'nCells' in var.dims:
                var = var.mean(dim='nCells')
            plt.figure(figsize=(5, 3))
            ax = plt.subplot(111)
            ax.plot(time_days, var, '-k')
            ax.set_ylabel(f'{field_name} ({field_units})')
            ax.set_xlabel('time (days)')
            plt.tight_layout(pad=0.5)
            plt.savefig(f'{field_name}_t.png', dpi=200)
            plt.close()

        ds = xr.load_dataset('conservationCheck.nc')
        fields = {'accumulatedFrazilFlux': r'kg s$^{-1}$',
                  'accumulatedFrazilHeatFlux': r'W s$^{-1}$',
                  'accumulatedFrazilSalinityFlux': r'PSU s$^{-1}$',
                  'absoluteEnergyError': '',
                  'initialSalt': '',
                  'finalSalt': '',
                  'saltChange': '',
                  'absoluteSaltError': '',
                  'absoluteMassError': ''}
        time = ds['daysSinceStartOfSim']
        time_days = time.values.astype("float64") / ns_per_day
        for field_name, field_units in fields.items():
            if field_name not in ds.keys():
                print(f'{field_name} not present in output.nc')
                continue
            var = ds[field_name]
            plt.figure(figsize=(5, 3))
            ax = plt.subplot(111)
            ax.plot(time_days[1:], var[1:], '-k')
            ax.set_ylabel(f'{field_name} ({field_units})')
            ax.set_xlabel('time (days)')
            plt.tight_layout(pad=0.5)
            plt.savefig(f'{field_name}_t.png', dpi=200)
            plt.close()
