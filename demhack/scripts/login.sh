ROOT="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; cd .. ; pwd -P )" 
export PYTHONPATH=${PYTHONPATH}:$ROOT
$ROOT/env/bin/python3 $ROOT/login.py
