#!/bin/bash

: ${PYTHON:=python2}
: ${NAME:=blah}

for pattern in '[01]{,10}' '\d+' '.*' '.*.*.*' '(?:[a-z]{,10}){,1000}' '(?:[a-z]{,100}){,1000}' '(?:(?:[a-z]{,100}){,100}){,100}'; do
  ${PYTHON} $(dirname "$0")/bench.py "$pattern" "$NAME"
  if [[ $? -eq 1 ]]; then break; fi
done
