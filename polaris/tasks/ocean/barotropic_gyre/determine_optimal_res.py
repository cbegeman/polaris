from scipy.special import lambertw

omega = lambertw(1).real
nu = 4e2
beta = 1e-11
L_ideal = ((nu / beta) / (1 / omega)) ** (1 / 3)
print(
    f'Recommended domain length is {L_ideal} m for '  # / 1.0e3:02g
    f'nu = {nu} and beta = {beta}, omega = {1 / omega}'
)
eps = nu / (beta * (L_ideal**3.0))
delta_m = eps ** (1.0 / 3.0)
print(f'eps = {eps}, delta_m = {delta_m}')
