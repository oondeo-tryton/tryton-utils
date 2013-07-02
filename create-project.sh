#!/bin/bash

if [[ -z "$1" || -z "$2" ]]; then
	echo "$0 project_name openerp_version"
	exit
fi
project_name=$1
openerp_version=$2

if [[ -e "$project_name" ]]; then
	echo "Project $project_name already exists."
	exit
fi

mkdir $project_name
pushd $project_name

touch local.cfg
echo "[buildout]" >> local.cfg
echo "auto-checkout += *" >> local.cfg
echo "[sources]" >> local.cfg

hg clone ssh://hg@bitbucket.org/nantic/tryton-buildout buildout
pushd buildout
python bootstrap.py
./build/bin/buildout -c base.cfg
./build/bin/buildout -c buildout.cfg
popd
pushd utils
./script-symlinks.sh
popd
hg init
