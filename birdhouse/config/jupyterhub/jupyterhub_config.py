import os
from os.path import join
import logging
import subprocess

from dockerspawner import DockerSpawner

c = get_config()  # noqa  # can be called directy without import because injected by IPython

c.JupyterHub.bind_url = 'http://:8000/jupyter'

## Whether to shutdown single-user servers when the Hub shuts down.
c.JupyterHub.cleanup_servers = False

c.JupyterHub.hub_ip = 'jupyterhub'

c.JupyterHub.authenticator_class = 'jupyterhub_magpie_authenticator.MagpieAuthenticator'
c.MagpieAuthenticator.magpie_url = "http://magpie:2001"
c.MagpieAuthenticator.public_fqdn = "10.0.2.15"
c.MagpieAuthenticator.authorization_url = "http://twitcher:8000/ows/verify/jupyterhub"

if os.getenv("JUPYTERHUB_CRYPT_KEY"):
    c.MagpieAuthenticator.enable_auth_state = True
    c.MagpieAuthenticator.refresh_pre_spawn = True
    c.MagpieAuthenticator.auth_refresh_age = int("60")

c.JupyterHub.cookie_secret_file = '/persist/jupyterhub_cookie_secret'
c.JupyterHub.db_url = '/persist/jupyterhub.sqlite'

c.JupyterHub.template_paths = ['/custom_templates']

class CustomDockerSpawner(DockerSpawner):
    @property
    def escaped_name(self):
        """
        Return the username without escaping. This ensures that mounted directories on the
        host machine are discovered properly since we expect the username to match the username
        set by Magpie.
        """
        return self.user.name

    async def start(self):
        if(os.environ['MOUNT_IMAGE_SPECIFIC_NOTEBOOKS'] == 'true'):
            host_dir = join(os.environ['JUPYTERHUB_USER_DATA_DIR'], 'tutorial-notebooks-specific-images')

            # Mount a volume with a tutorial-notebook subfolder corresponding to the image name, if it exists
            # The names are defined in the JUPYTERHUB_IMAGE_SELECTION_NAMES variable.
            image_name = self.user_options.get('image')
            if(os.path.isdir(join(host_dir, image_name))):
                self.volumes[join(host_dir, image_name)] = {
                    "bind": '/notebook_dir/tutorial-notebooks',
                    "mode": "ro"
                }
            else:
                # Try again, removing any colons and any following text. Useful if the image name contains
                # the version number, which should not be used in the directory name.
                image_name = image_name.split(':')[0]
                if(os.path.isdir(join(host_dir, image_name))):
                    self.volumes[join(host_dir, image_name)] = {
                        "bind": '/notebook_dir/tutorial-notebooks',
                        "mode": "ro"
                    }
        else:
            # Mount the entire tutorial-notebooks directory
            self.volumes[join(os.environ['JUPYTERHUB_USER_DATA_DIR'], "tutorial-notebooks")] = {
                "bind": "/notebook_dir/tutorial-notebooks",
                "mode": "ro"
            }
        return await super().start()

c.JupyterHub.spawner_class = CustomDockerSpawner

# Selects the first image from the list by default
c.DockerSpawner.image = os.environ['DOCKER_NOTEBOOK_IMAGES'].split()[0]
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = os.environ['DOCKER_NETWORK_NAME']

notebook_dir = '/notebook_dir'
jupyterhub_data_dir = os.environ['JUPYTERHUB_USER_DATA_DIR']
container_workspace_dir = join(notebook_dir, "writable-workspace")
container_home_dir = join(container_workspace_dir, ".home")

c.DockerSpawner.notebook_dir = notebook_dir
c.DockerSpawner.environment = {
    "HOME": container_home_dir,
    # https://docs.bokeh.org/en/latest/docs/user_guide/jupyter.html#jupyterhub
    # Issue https://github.com/bokeh/bokeh/issues/12090
    # Post on Panel forum:
    # https://discourse.holoviz.org/t/how-to-customize-the-display-url-from-panel-serve-for-use-behind-jupyterhub-with-jupyter-server-proxy/3571
    # Issue about Panel Preview: https://github.com/holoviz/panel/issues/3440
    "PAVICS_HOST_URL": "https://10.0.2.15",
    # https://docs.dask.org/en/stable/configuration.html
    # https://jupyterhub-on-hadoop.readthedocs.io/en/latest/dask.html
    "DASK_DISTRIBUTED__DASHBOARD__LINK": "https://10.0.2.15{JUPYTERHUB_SERVICE_PREFIX}proxy/{port}/status"
}

host_user_data_dir = join(os.environ['WORKSPACE_DIR'], "{username}")
c.DockerSpawner.volumes = {host_user_data_dir: container_workspace_dir}

# Case for the cowbird setup, where the workspace_dir contains a symlink to the jupyterhub dir.
# The jupyterhub dir must also be mounted in this case.
if os.environ['WORKSPACE_DIR'] != jupyterhub_data_dir:
    c.DockerSpawner.volumes[join(jupyterhub_data_dir, "{username}")] = {
        "bind": join(jupyterhub_data_dir, "{username}"),
        "mode": "rw"
    }
    c.DockerSpawner.volumes[join(os.environ['WORKSPACE_DIR'], os.environ['PUBLIC_WORKSPACE_WPS_OUTPUTS_SUBDIR'])] = {
        "bind": join(notebook_dir, os.environ['PUBLIC_WORKSPACE_WPS_OUTPUTS_SUBDIR']),
        "mode": "ro"
    }

container_gdrive_settings_path = join(container_home_dir, ".jupyter/lab/user-settings/@jupyterlab/google-drive/drive.jupyterlab-settings")
host_gdrive_settings_path = os.environ['JUPYTER_GOOGLE_DRIVE_SETTINGS']

if len(host_gdrive_settings_path) > 0:
    c.DockerSpawner.volumes[host_gdrive_settings_path] = {
        "bind": container_gdrive_settings_path,
        "mode": "ro"
    }

readme = os.environ.get('JUPYTERHUB_README', default="")
if readme != "":
    c.DockerSpawner.volumes[readme] = {
        "bind": join(notebook_dir, "README.ipynb"),
        "mode": "ro"
    }

def create_dir_hook(spawner):
    username = spawner.user.name
    jupyterhub_user_dir = join(jupyterhub_data_dir, username)

    if not os.path.exists(jupyterhub_user_dir):
        os.mkdir(jupyterhub_user_dir, 0o755)

    subprocess.call(["chown", "-R", f"{os.environ['USER_WORKSPACE_UID']}:{os.environ['USER_WORKSPACE_GID']}",
                     jupyterhub_user_dir])

    if os.environ['WORKSPACE_DIR'] != jupyterhub_data_dir:
        # Case for cowbird setup. The workspace directory should also have the user's ownership,
        # to have working volume mounts with the DockerSpawner.
        workspace_user_dir = join(os.environ['WORKSPACE_DIR'], username)
        if not os.path.exists(workspace_user_dir):
            raise FileNotFoundError(f"The user {username}'s workspace doesn't exist in the workspace directory, "
                                    "but should have been created by Cowbird already.")
        subprocess.call(["chown", f"{os.environ['USER_WORKSPACE_UID']}:{os.environ['USER_WORKSPACE_GID']}",
                         workspace_user_dir])

    if username == os.environ['JUPYTER_DEMO_USER']:
        # Restrict resources for the public demo user
        # CPU limit, seems not honored by DockerSpawner
        spawner.cpu_limit = float(os.environ['JUPYTER_DEMO_USER_CPU_LIMIT'])
        spawner.mem_limit = os.environ['JUPYTER_DEMO_USER_MEM_LIMIT']

c.Spawner.pre_spawn_hook = create_dir_hook

## Disable per-user configuration of single-user servers.
c.Spawner.disable_user_config = True

c.DockerSpawner.default_url = '/lab'
c.DockerSpawner.remove = True  # delete containers when servers are stopped

c.DockerSpawner.image_whitelist = {
    'jupyter/scipy-notebook': 'jupyter/scipy-notebook',
    'jupyter/r-notebook': 'jupyter/r-notebook',
    'jupyter/tensorflow-notebook': 'jupyter/tensorflow-notebook',
    'jupyter/datascience-notebook': 'jupyter/datascience-notebook',
    'jupyter/pyspark-notebook': 'jupyter/pyspark-notebook',
    'jupyter/all-spark-notebook': 'jupyter/all-spark-notebook',
}
    # noqa
c.DockerSpawner.pull_policy = "always"  # for images not using pinned version
c.DockerSpawner.debug = True
c.JupyterHub.log_level = logging.DEBUG

c.Spawner.debug = True

## Timeout (in seconds) to wait for spawners to initialize
c.JupyterHub.init_spawners_timeout = 20  # default 10

## Timeout (in seconds) before giving up on a spawned HTTP server
c.Spawner.http_timeout = 60  # default 30

## Timeout (in seconds) before giving up on starting of single-user server.
c.Spawner.start_timeout = 120  # default 60

## Extra arguments to be passed to the single-user server.
c.Spawner.args = [
    # Allow non-empty directory deletion which enable recursive dir deletion.
    # https://jupyter-server.readthedocs.io/en/latest/other/full-config.html
    "--FileContentsManager.always_delete_dir=True",
    ]

c.DockerSpawner.extra_host_config = {
    # start init pid 1 process to reap defunct processes
    'init': True,
    }

c.Authenticator.admin_users = {'admin'}     # noqa

## Force refresh of auth prior to spawn.
# Do nothing right now, pending implementation of
# MagpieAuthenticator.refresh_user() (see
# https://github.com/Ouranosinc/jupyterhub/issues/2)
c.Authenticator.refresh_pre_spawn = True

## Blacklist of usernames that are not allowed to log in.
# https://jupyterhub.readthedocs.io/en/stable/api/auth.html
#
# For security reasons, block user with known hardcoded public password or
# non real Jupyter users.
blocked_users = {'authtest', '${CATALOG_USERNAME}', 'anonymous'}
c.Authenticator.blacklist = blocked_users  # v0.9+
c.Authenticator.blocked_users = blocked_users  # v1.2+


# ------------------------------------------------------------------------------
# Shutdown idle user server based on configured timeouts.
# ------------------------------------------------------------------------------
# Timeout (in seconds, default: 3 days) to shut down the user server when no kernels or terminals
# are running and there is no activity. If undefined or set to zero, the feature will not be enabled.
jupyter_idle_server_cull_timeout = int("600" or 0)
if jupyter_idle_server_cull_timeout:
    c.Spawner.args.append('--NotebookApp.shutdown_no_activity_timeout={}'.format(jupyter_idle_server_cull_timeout))
# Timeout (in seconds, default: 1 day) after which individual
# user kernels/terminals are considered idle and ready to be culled.
jupyter_idle_kernel_cull_timeout = int("10" or 0)
# Interval (in seconds, default: half of timeout) on which to check for idle kernels exceeding the cull timeout value.
jupyter_idle_kernel_cull_interval = int("" or 0)
if jupyter_idle_kernel_cull_timeout:
    if not jupyter_idle_kernel_cull_interval or jupyter_idle_kernel_cull_interval > jupyter_idle_kernel_cull_timeout:
        jupyter_idle_kernel_cull_interval = max(1, int(jupyter_idle_kernel_cull_timeout / 2))
    c.Spawner.args.extend([
        '--MappingKernelManager.cull_idle_timeout={}'.format(jupyter_idle_kernel_cull_timeout),
        '--MappingKernelManager.cull_interval={}'.format(jupyter_idle_kernel_cull_interval),
        '--TerminalManager.cull_inactive_timeout={}'.format(jupyter_idle_kernel_cull_timeout),
        '--TerminalManager.cull_interval={}'.format(jupyter_idle_kernel_cull_interval),
    ])
# Culling kernels which have one or more connections for idle but open notebooks and/or terminals.
# Otherwise, browser tabs, notebooks and terminals all have to be closed for culling to work.
if jupyter_idle_server_cull_timeout or jupyter_idle_kernel_cull_timeout:
    c.Spawner.args.extend([
        '--MappingKernelManager.cull_connected=True',
        '--TerminalManager.cull_connected=True',
    ])

# ------------------------------------------------------------------------------
# Configuration overrides
# ------------------------------------------------------------------------------


# do not pull docker iamge updates each time
c.DockerSpawner.pull_policy = "ifnotpresent"

# allow HTTP requests to /jupyter/hub/api using the following token
# {Authorization: Token <token>}
c.JupyterHub.services = [
    {
        "name": "service-admin",
        "api_token": "admin-token",
    },
]
c.JupyterHub.load_roles = [
    {
        "name": "service-role",
        "scopes": [
            # specify the permissions the token should have
            "admin:users",
            "admin:servers",
            "access:servers",
            "proxy"
        ],
        "services": [
            # assign the service the above permissions
            "service-admin",
        ],
    }
]

# mount additional local notebook locations to imitate the results from auto-deploy script:
# - birdhouse/pavics-jupyter-base/scheduler-jobs/deploy_data_pavics_jupyter.env
# - birdhouse/pavics-jupyter-base/scheduler-jobs/deploy_data_specific_image
class OverrideDockerSpawner(CustomDockerSpawner):
    async def start(self):
        self.volumes["/home/francis/dev/daccs/pavics-sdi/"] = {
            "bind": "/home/francis/dev/daccs/pavics-sdi/",
            "mode": "ro",
        }
        self.volumes["/home/francis/dev/daccs/pavics-jupyter-images/"] = {
            "bind": "/home/francis/dev/daccs/pavics-jupyter-images/",
            "mode": "ro",
        }
        return await super().start()

c.JupyterHub.spawner_class = OverrideDockerSpawner

    # noqa
