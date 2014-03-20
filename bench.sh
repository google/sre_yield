#!/bin/bash

for pattern in '[01]{,10}' '\d+' '.*' '.*.*.*' '(?:[a-z]{,10}){,1000}'; do
  python2 bench.py "$pattern"
done
