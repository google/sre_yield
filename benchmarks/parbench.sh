#!/bin/bash
: ${PYTHON:=python2}
: ${NAME:=blah}


echo -n > log  #truncate
/bin/echo '[01]{,10}' '\\d+' '.*' '.*.*.*' '(?:[a-z]{,10}){,1000}' '(?:[a-z]{,100}){,1000}' '(?:(?:[a-z]{,100}){,100}){,100}' |
xargs -P6 -n1 /bin/sh -c 'text=$('"${PYTHON}"' bench.py "$0" '"${NAME}"'); echo "$text" | tee -a log'
