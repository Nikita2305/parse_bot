ROOT="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; cd .. ; pwd -P )" 
# export PYTHONPATH=${PYTHONPATH}:$ROOT

if [ "$1" == "" ]; then
    echo "Paste .config file according to README"
    exit
fi

$ROOT/env/bin/python3 $ROOT/login.py $1
