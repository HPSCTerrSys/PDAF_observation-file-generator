# Shared Utilities (`utils/`)

### `utils/nc_attributes.py`

Writes standard provenance attributes to any open `netCDF4.Dataset`:

```python
import utils.nc_attributes as pdaf_obs_utils
pdaf_obs_utils.set_netcdf_attributes(dst, scriptname="create_crns_obs.py", setup="my_run")
```

Attributes written:

| Attribute                   | Content                                                                                                                            |
|-----------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| `Observations_generated_by` | Username of the person running the script                                                                                          |
| `obs_for_setup`             | Value of the `--setup` argument                                                                                                    |
| `generated_on_date`         | ISO 8601 date (YYYY-MM-DD)                                                                                                         |
| `generated_with_script`     | Script filename                                                                                                                    |
| `git-repository`            | Remote origin URL of the git repository                                                                                            |
| `git-hash`                  | Short commit hash (10 chars); key is suffixed with `(dirty worktree)` if uncommitted changes are present, and a warning is printed |
