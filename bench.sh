#!/bin/bash

for pattern in '[01]{,10}' '\d+' '.*' '.*.*.*' '(?:[a-z]{,10}){,1000}' '(?:[a-z]{,100}){,1000}' '(?:(?:[a-z]{,100}){,100}){,100}'; do
  python2 bench.py "$pattern"
done
