import matplotlib.pyplot as plt
from scipy.stats import genextreme, chi2
from statsmodels.stats.multitest import fdrcorrection

import numpy as np
import xarray as xr

def plot_hist_and_fit(data, params, filename):
    plt.figure(figsize=(10, 6))
    
    # Plot histogram of the data
    plt.hist(data, bins=30, density=True, alpha=0.6, color='g', label='Data Histogram')
    
    # Plot the fitted GEV PDF
    x_min = genextreme.ppf(0.01, *params) # 1th percentile
    x_max = genextreme.ppf(0.99, *params) # 99th percentile
    x = np.linspace(x_min, x_max, 500)

    pdf_fitted = genextreme.pdf(x, *params)
    plt.plot(x, pdf_fitted, 'r-', lw=2, label='Fitted GEV PDF')
    
    plt.title('Generalized Extreme Value (GEV) Fit to Data')
    plt.xlabel('Value')
    plt.ylabel('Probability Density')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)

def gev_fit_wrapper(data, dim='nCells'):
    """
    Fits the generalized extreme value distribution to 1D data
    and returns the parameters (c, loc, scale) as a 1D array.
    """
    if dim is None:
        params = genextreme.fit(data.values)
        return params

    if dim not in ds.dims:
        print(f'dataset does not have dimension {dim} to loop over')
        return

    nvalues = data.sizes[dim]
    params = np.zeros((nvalues, 3))
    for i in range(nvalues):
        params[i, :] = genextreme.fit(data.values[:,i])
    return params

def log_likelihood_wrapper(data, params, dim='nCells'):
    if dim is None:
        log_likelihood = np.sum(
            genextreme.logpdf(data.values, *params)
        )
        return log_likelihood

    if dim not in ds.dims:
        print(f'dataset does not have dimension {dim} to loop over')
        return

    nvalues = data.sizes[dim]
    log_likelihood = np.zeros((nvalues))
    for i in range(nvalues):
        log_likelihood[i] = np.sum(
            genextreme.logpdf(data.values[:,i], *params[i,:])
        )
    return log_likelihood

def compute_pvalue_from_loglikelihood(x1, x2):

    # Fit separate models
    params1 = gev_fit_wrapper(x1)
    plot_hist_and_fit(x1.values[:,0], params1[0,:], 'x1_hist_and_fit.png')
    params2 = gev_fit_wrapper(x2)
    
    # Fit pooled model
    data_pooled = xr.concat([x1, x2], dim='Time')
    params_pooled = gev_fit_wrapper(data_pooled)

    # Compute log-likelihoods
    log1 = log_likelihood_wrapper(x1, params1)
    log2 = log_likelihood_wrapper(x2, params2)
    log_pooled = log_likelihood_wrapper(data_pooled, params_pooled)
    
    # Likelihood ratio statistic
    Lambda = 2 * ((log1 + log2) - log_pooled)

    p_value = 1 - chi2.cdf(Lambda, df=3)  # 3 parameter difference (μ, σ, ξ)

    return p_value

member_name = 'highFrequencyOutput'
var = 'temperatureAtSurface'

mesh_filename = '/global/cfs/cdirs/e3sm/inputdata/ocn/mpas-o/SOwISC12to30E3r3/mpaso.SOwISC12to30E3r3.rstFromG-chrysalis.20240829.nc'
filename1 = f'20250622.v3.SORRME3r3.CRYO1850.alfred3.kpp-tuning.pm-cpu.mpaso.hist.am.{member_name}.0010.nc'
filename2 = f'20250622.v3.SORRME3r3.CRYO1850.alfred3.kpp-tuning.pm-cpu.mpaso.hist.am.{member_name}.0020.nc'

ds1 = xr.open_dataset(filename1)
ds2 = xr.open_dataset(filename2)

ds_mesh = xr.open_dataset(mesh_filename)
mask = ds_mesh.latCell * 180 / np.pi < -80.
ds1 = ds1.where(mask, drop=True)
ds2 = ds2.where(mask, drop=True)

x1 = ds1[var]
x2 = ds2[var]

p_value = compute_pvalue_from_loglikelihood(x1, x2)

passes_logical, p_value_corr = fdrcorrection(p_value, alpha=0.01, method='indep', is_sorted=False)
print(f'{np.sum(passes_logical.values)} of {np.sum(lat_mask.values)} cells are from a different population')
