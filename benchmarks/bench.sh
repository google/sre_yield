#!/bin/bash
#
# Copyright 2011-2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

: ${PYTHON:=python2}
: ${NAME:=blah}

for pattern in '[01]{,10}' '\d+' '.*' '.*.*.*' '(?:[a-z]{,10}){,1000}' '(?:[a-z]{,100}){,1000}' '(?:(?:[a-z]{,100}){,100}){,100}'; do
  ${PYTHON} $(dirname "$0")/bench.py "$pattern" "$NAME"
  if [[ $? -eq 1 ]]; then break; fi
done
