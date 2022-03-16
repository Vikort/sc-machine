#!/usr/bin/env bash

set -eo pipefail

pip3 install --user -r requirements.txt

mkdir build
pushd build

cmake .. -DCMAKE_BUILD_TYPE=${BUILD_TYPE} -DSC_AUTO_TEST=ON -DSC_BUILD_SCTP=OFF -DBUILD_TESTING=ON -DSC_KPM_SCP=OFF
make -j4

../bin/sc-builder -i ../tools/builder/tests/kb -o ../bin/sc-builder-test-repo -c -f

popd