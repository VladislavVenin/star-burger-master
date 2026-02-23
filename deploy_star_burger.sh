#!/bin/bash

set -x

send_rollbar_deploy() {
    local status=$1
    local comment=$2
    curl --request POST \
         --url https://api.rollbar.com/api/1/deploy \
         --header 'X-Rollbar-Access-Token: 2d45d450fc4c46ba917967d3378ff0e4' \ # замените на свой токен 
         --header 'accept: application/json' \
         --header 'content-type: application/json' \
         --data "$(cat <<EOF
{
  "environment": "production",
  "revision": "$(git --git-dir=/opt/star-burger-master/.git --work-tree=/opt/star-burger-master/ rev-parse HEAD)",
  "local_username": "$(whoami)",
  "comment": "$comment",
  "status": "$status"
}
EOF
)"
}

send_rollbar_deploy "started" "Deployment started"

{
    git pull || { echo "Git pull failed"; send_rollbar_deploy "failed" "Git pull failed"; exit 1; }
    source venv/bin/activate
    pip install -r requirements.txt || { echo "Pip install failed"; send_rollbar_deploy "failed" "Pip install failed"; exit 1; }
    npm install || { echo "NPM install failed"; send_rollbar_deploy "failed" "NPM install failed"; exit 1; }
    python ./manage.py collectstatic --noinput || { echo "Collectstatic failed"; send_rollbar_deploy "failed" "Collectstatic failed"; exit 1; }
    python ./manage.py makemigrations --dry-run --check || { echo "Makemigrations failed"; send_rollbar_deploy "failed" "Makemigrations failed"; exit 1; }
    python ./manage.py migrate --noinput || { echo "Migrate failed"; send_rollbar_deploy "failed" "Migrate failed"; exit 1; }
    systemctl restart star-burger-py || { echo "Failed to restart star-burger-py"; send_rollbar_deploy "failed" "Failed to restart star-burger-py"; exit 1; }

    echo "Website successfully deployed"

    send_rollbar_deploy "succeeded" "Deployment succeeded"
} || {
    echo "Error encountered. Deployment failed." >&2
    send_rollbar_deploy "failed" "Deployment failed"
    exit 1
}

deactivate