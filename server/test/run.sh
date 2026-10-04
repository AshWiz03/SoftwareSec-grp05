#!/bin/sh

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

pytest test -svv -m "not manual"\
  --base-url=http://server:5000 \
  --junitxml="/app/unit_test_results/results_${TIMESTAMP}.xml"

STATUS=$?

exit $STATUS