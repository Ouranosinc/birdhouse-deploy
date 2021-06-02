#!/bin/sh
# Script to trigger deployment, only if needed.
#
# If checkout is behind, then trigger deployment, else do nothing.
#
# In divergent case (both behind and ahead at the same time), do nothing as
# well to prevent deploy loop on a dev machine.
#
# One time Setup:
#
#   Follow same instructions in deploy.sh.

if [ ! -z "$AUTODEPLOY_SILENT" ]; then
    LOG_FILE="/var/log/PAVICS/autodeploy.log"
    exec >>$LOG_FILE 2>&1
fi

usage() {
    echo "USAGE: $0 <path to folder with docker-compose.yml file> [path to env.local]"
}

COMPOSE_DIR="$1"
ENV_LOCAL_FILE="$2"

if [ -z "$COMPOSE_DIR" ]; then
    echo "ERROR: please provide path to PAVICS docker-compose dir." 1>&2
    usage
    exit 2
else
    shift
fi

if [ -z "$ENV_LOCAL_FILE" ]; then
    ENV_LOCAL_FILE="$COMPOSE_DIR/env.local"
else
    shift
fi

COMPOSE_DIR="`realpath "$COMPOSE_DIR"`"

if [ ! -f "$COMPOSE_DIR/docker-compose.yml" ]; then
    echo "ERROR: missing docker-compose.yml in '$COMPOSE_DIR'" 1>&2
    exit 2
fi

if [ ! -f "$ENV_LOCAL_FILE" ]; then
    echo "ERROR: env.local not found at '$ENV_LOCAL_FILE'" 1>&2
    exit 2
fi

# Setup COMPOSE_DIR and PWD for sourcing env.local.
# Prevent un-expected difference when this script is run inside autodeploy
# container and manually from the host.
cd $COMPOSE_DIR


should_trigger() {
    EXTRA_REPO="`git rev-parse --show-toplevel`"

    DEPLOY_KEY="$AUTODEPLOY_DEPLOY_KEY_ROOT_DIR/`basename "$EXTRA_REPO"`_deploy_key"
    DEFAULT_DEPLOY_KEY="$AUTODEPLOY_DEPLOY_KEY_ROOT_DIR/id_rsa_git_ssh_read_only"
    if [ ! -e "$DEPLOY_KEY" -a -e "$DEFAULT_DEPLOY_KEY" ]; then
        DEPLOY_KEY="$DEFAULT_DEPLOY_KEY"
    fi
    DEPLOY_KEY_DISPLAY=""

    export GIT_SSH_COMMAND=""  # git ver 2.3+
    if [ -e "$DEPLOY_KEY" ]; then
        DEPLOY_KEY_DISPLAY=" deploy_key='$DEPLOY_KEY'"
        export GIT_SSH_COMMAND="ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o IdentityFile=$DEPLOY_KEY"
    else
        unset GIT_SSH_COMMAND
    fi

    echo "triggerdeploy: checking repo '$EXTRA_REPO'$DEPLOY_KEY_DISPLAY"

    # fetch remote branches, not affecting current checkout
    git fetch --prune --all

    CURRENT_BRANCH="`git rev-parse --abbrev-ref HEAD`"

    # find out if we are behind and/or ahead remote tracking branch
    TMP_SAVE_FILE="/tmp/triggerdeploy-behindcnt.txt"
    echo "BEHIND_CNT=-1" > $TMP_SAVE_FILE
    echo "AHEAD_CNT=-1" >> $TMP_SAVE_FILE
    git for-each-ref --format="%(refname:short) %(upstream:short)" refs/heads | \
    while read local remote
    do
        [ -z "$remote" ] && continue
        git show-branch remotes/$remote || continue
        [ "$local" != "$CURRENT_BRANCH" ] && continue
        BEHIND_CNT="`git rev-list --right-only --count ${local}...${remote}`"
        AHEAD_CNT="`git rev-list --left-only --count ${local}...${remote}`"
        echo "BEHIND_CNT=$BEHIND_CNT" >> $TMP_SAVE_FILE
        echo "AHEAD_CNT=$AHEAD_CNT" >> $TMP_SAVE_FILE
        break
    done
    . $TMP_SAVE_FILE
    rm $TMP_SAVE_FILE

    # trigger deploy if the behind count is greater than zero and ahead count is
    # less than or equal zero
    if [ "$BEHIND_CNT" -gt 0 ]; then
        if [ "$AHEAD_CNT" -le 0 ]; then
            echo "triggerdeploy: repo '$EXTRA_REPO' is behind will trigger deploy"
            return 0
        else
            echo "triggerdeploy: do nothing, repo '$EXTRA_REPO' is both behind and ahead (divergent), must be a devel repo"
            return 1
        fi
    else
        echo "triggerdeploy: repo '$EXTRA_REPO' is up-to-date or ahead, no deploy needed"
        return 1
    fi
}


START_TIME="`date -Isecond`"
echo "==========
triggerdeploy START_TIME=$START_TIME"

. ./default.env

# Read AUTODEPLOY_EXTRA_REPOS
. $ENV_LOCAL_FILE

set -x

SHOULD_TRIGGER=""
for adir in $COMPOSE_DIR $AUTODEPLOY_EXTRA_REPOS; do
    if [ -d "$adir" ]; then
        cd $adir

        if should_trigger; then
            SHOULD_TRIGGER=1
            break
        fi
    else
        echo "WARNING: extra repo '$adir' do not exist"
    fi
done

EXIT_CODE=0
if [ -n "$SHOULD_TRIGGER" ]; then
    cd $COMPOSE_DIR
    TMP_SCRIPT="/tmp/latestdeploy.sh"
    # get latest version of deploy script on same branch
    CURRENT_REMOTE_BRANCH="`git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`"
    git show $CURRENT_REMOTE_BRANCH:./deployment/deploy.sh > $TMP_SCRIPT

    chmod a+x $TMP_SCRIPT
    $TMP_SCRIPT $COMPOSE_DIR $ENV_LOCAL_FILE
    EXIT_CODE=$?
    rm $TMP_SCRIPT
fi

set +x

echo "
triggerdeploy finished START_TIME=$START_TIME
triggerdeploy finished   END_TIME=`date -Isecond`"

exit $EXIT_CODE


# vi: tabstop=8 expandtab shiftwidth=4 softtabstop=4
