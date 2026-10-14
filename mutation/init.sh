#!/bin/sh

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
RESULTS_DIR="/app/mutation_test_results"
mkdir -p "$RESULTS_DIR"

mutmut run
RUN_STATUS=$?

mutmut results > "$RESULTS_DIR/results_${TIMESTAMP}.txt"

{
  mutmut results | grep survived | awk '{print $1}' | sed 's/://' | while read -r id; do
    echo "=== $id ==="
    mutmut show "$id"
    echo
  done
} > "$RESULTS_DIR/survivors_${TIMESTAMP}.txt"

exit $RUN_STATUS