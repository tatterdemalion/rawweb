#!/bin/bash

DIRECTORY=$1
pushd $DIRECTORY && for i in $(ls); do http -f PUT http://localhost:5000/api/ image@$i; done && popd

