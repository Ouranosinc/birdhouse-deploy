#!/bin/sh

# NOTE, this file and all the extra component pre/post scripts that it executes
# is used by the autodeploy mechanism inside a very minimalistic container,
# therefore:
#
# * When making change to this file or any extra component pre/post scripts,
#   should also test that it does not break the autodeploy.
#
# * Try to keep the same behavior/code, inside and outside of the
#   autodeploy container to catch error early with the autodeploy.

# list of all variables to be substituted in templates
#   some of these variables *could* employ provided values in 'default.env',
#   but they must ultimately be defined one way or another for the server to work
VARS='
  $PAVICS_FQDN
  $DOC_URL
  $SUPPORT_EMAIL
  $DATA_PERSIST_ROOT
  $DATA_PERSIST_SHARED_ROOT
'

# list of vars to be substituted in template but they do not have to be set in env.local
#   their default values are from 'default.env', so they do not have to be defined in 'env.local' if values are adequate
#   they usually are intended to provide additional features or extended customization of their behavior
#   when the value provided explicitly, it will be used instead of guessing it by inferred values from other variables
OPTIONAL_VARS='
  $PAVICS_FQDN_PUBLIC
  $SSL_CERTIFICATE
  $EXTRA_PYWPS_CONFIG
  $SERVER_NAME
  $SERVER_DESCRIPTION
  $SERVER_INSTITUTION
  $SERVER_SUBJECT
  $SERVER_TAGS
  $SERVER_DOCUMENTATION_URL
  $SERVER_RELEASE_NOTES_URL
  $SERVER_SUPPORT_URL
  $SERVER_LICENSE_URL
'

# we switch to the real directory of the script, so it still works when used from $PATH
# tip: ln -s /path/to/pavics-compose.sh ~/bin/
# Setup PWD for sourcing env.local.
cd "$(dirname "$(readlink -f "$0" || realpath "$0")")" || exit 1

# Setup COMPOSE_DIR for sourcing env.local.
# Prevent un-expected difference when this script is run inside autodeploy
# container and manually from the host.
COMPOSE_DIR="$(pwd)"

. "${COMPOSE_DIR}/scripts/read-configs.include.sh"
read_configs # this sets ALL_CONF_DIRS

. "${COMPOSE_DIR}/scripts/get-components-json.include.sh"
. "${COMPOSE_DIR}/scripts/get-services-json.include.sh"
. "${COMPOSE_DIR}/scripts/get-version-json.include.sh"

check_required_vars || exit $?

## check fails when root access is required to access this file.. workaround possible by going through docker daemon... but
# will add delay
# if [ ! -f $SSL_CERTIFICATE ]
# then
#   log ERROR "SSL certificate file $SSL_CERTIFICATE is missing"
#   exit 1
# fi

TIMEWAIT_REUSE=$(/sbin/sysctl -n  net.ipv4.tcp_tw_reuse)
if [ "${TIMEWAIT_REUSE}" -eq 0 ]
then
  log WARN "the sysctl net.ipv4.tcp_tw_reuse is not enabled. " \
       "It it suggested to set it to 1, otherwise the pavicscrawler may fail."
fi

export AUTODEPLOY_EXTRA_REPOS_AS_DOCKER_VOLUMES=""
for adir in $AUTODEPLOY_EXTRA_REPOS; do
  # 4 spaces in front of '--volume' is important
  AUTODEPLOY_EXTRA_REPOS_AS_DOCKER_VOLUMES="$AUTODEPLOY_EXTRA_REPOS_AS_DOCKER_VOLUMES
    --volume ${adir}:${adir}:rw"
done
export AUTODEPLOY_EXTRA_REPOS_AS_DOCKER_VOLUMES

# we apply all the templates
find $ALL_CONF_DIRS -name '*.template' 2>/dev/null |
  while read FILE
  do
    DEST=${FILE%.template}
    cat "${FILE}" | envsubst "$VARS" | envsubst "$OPTIONAL_VARS" > "${DEST}"
  done

SHELL_EXEC_FLAGS=
if [ "${BIRDHOUSE_LOG_LEVEL}" = "DEBUG" ]; then
  SHELL_EXEC_FLAGS=-x
fi

create_compose_conf_list # this sets COMPOSE_CONF_LIST
log INFO "Displaying resolved compose configurations:"
echo "COMPOSE_CONF_LIST="
echo ${COMPOSE_CONF_LIST} | tr ' ' '\n' | grep -v '^-f'

if [ x"$1" = x"info" ]; then
  log INFO "Stopping before execution of docker-compose command."
  exit 0
fi

if [ x"$1" = x"up" ]; then
  for adir in $ALL_CONF_DIRS; do
    COMPONENT_PRE_COMPOSE_UP="$adir/pre-docker-compose-up"
    if [ -x "$COMPONENT_PRE_COMPOSE_UP" ]; then
      log INFO "Executing '$COMPONENT_PRE_COMPOSE_UP'"
      sh ${SHELL_EXEC_FLAGS} "$COMPONENT_PRE_COMPOSE_UP"
    fi
  done
fi

# the PROXY_SECURE_PORT is a little trick to make the compose file invalid without the usage of this wrapper script
PROXY_SECURE_PORT=443 HOSTNAME=${PAVICS_FQDN} docker-compose ${COMPOSE_CONF_LIST} $*
ERR=$?

# execute post-compose function if exists and no error occurred
type post-compose 2>&1 | grep 'post-compose is a function' > /dev/null
if [ $? -eq 0 ]
then
  [ ${ERR} -gt 0 ] && { log ERROR "Error occurred with docker-compose, not running post-compose"; exit $?; }
  post-compose $*
fi


while [ $# -gt 0 ]
do
  if [ x"$1" = x"up" ]; then
    # we restart the proxy after an up to make sure nginx continue to work if any container IP address changes
    PROXY_SECURE_PORT=443 HOSTNAME=${PAVICS_FQDN} docker-compose ${COMPOSE_CONF_LIST} restart proxy

    # run postgres post-startup setup script
    # Note: this must run before the post-docker-compose-up scripts since some may expect postgres databases to exist
    postgres_id=$(PROXY_SECURE_PORT=443 HOSTNAME=${PAVICS_FQDN} docker-compose ${COMPOSE_CONF_LIST} ps -q postgres 2> /dev/null)
    if [ ! -z "$postgres_id" ]; then
      docker exec ${postgres_id} /postgres-setup.sh
    fi

    for adir in $ALL_CONF_DIRS; do
      COMPONENT_POST_COMPOSE_UP="$adir/post-docker-compose-up"
      if [ -x "$COMPONENT_POST_COMPOSE_UP" ]; then
        log INFO "Executing '$COMPONENT_POST_COMPOSE_UP'"
        sh ${SHELL_EXEC_FLAGS} "$COMPONENT_POST_COMPOSE_UP"
      fi
    done

    # Note: This command should stay last, as it can take a while depending on network and drive speeds
    # immediately cache the new notebook images for faster startup by JupyterHub
    for IMAGE in ${DOCKER_NOTEBOOK_IMAGES}
    do
      docker pull $IMAGE
    done

  fi
  shift
done


# vi: tabstop=8 expandtab shiftwidth=2 softtabstop=2
