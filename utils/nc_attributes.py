'''
Set NetCDF Attributes
'''
import getpass
import datetime
import warnings

try:
    import git
    _GIT_AVAILABLE = True
except ImportError:
    _GIT_AVAILABLE = False


def set_netcdf_attributes(dst, scriptname, setup="undefined"):
    """
    Set attributes of NetCDF files

    Parameters
    ----------
    dst : netCDF4.Dataset
        Dataset to write attributes to.

    scriptname : string
        Script that generates the NetCDF file.

    setup : string
        Setup, for which the observation are created.

    """
    # Attributes
    dst.setncattr("Observations_generated_by", getpass.getuser())
    dst.setncattr("obs_for_setup", setup)
    dst.setncattr("generated_on_date",
                  datetime.datetime.today().strftime("%Y-%m-%d"))
    dst.setncattr("generated_with_script", scriptname)

    # Fallback option: git not available
    if not _GIT_AVAILABLE:
        warnings.warn("`import git` not available.", UserWarning)
        dst.setncattr("git-repository", "unknown (gitpython not installed)")
        dst.setncattr("git-hash", "unknown (gitpython not installed)")
        return

    try:
        repo = git.Repo(search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        # Fallback option: not in a git repository
        warnings.warn("Not inside a git repository.", UserWarning)
        dst.setncattr("git-repository", "unknown (not a git repository)")
        dst.setncattr("git-hash", "unknown (not a git repository)")
        return

    # Derive repository identity from remote URL if available
    try:
        repo_url = repo.remotes.origin.url
    except AttributeError:
        repo_url = "unknown (no remote 'origin')"
        dst.setncattr("git-repository", repo_url)

    # Check for modified files using `git ls-files -m` and issue warning if
    # there are any
    if len(repo.git.ls_files(m=True)) > 0:
        warnings.warn("Dirty worktree in git repository! Check `git status`",
                      UserWarning)
        dst.setncattr("git-hash (dirty worktree)", repo.head.object.hexsha[:10])
    else:
        dst.setncattr("git-hash", repo.head.object.hexsha[:10])
