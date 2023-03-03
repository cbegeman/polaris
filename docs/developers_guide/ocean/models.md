(dev-models)=

# Models

Polaris is designed to support multiple ocean models.

(dev-supported-models)=

## Supported Models

### MPAS-Ocean

The minimal set of initial state variables that must be defined in the `initial_state` step of each test case is:

```
temperature
salinity
normalVelocity
fCell
fEdge
fVertex
```


