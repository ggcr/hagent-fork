#!/bin/bash

rm -f *.log
rm -f *.yaml
rm -rf equiv_check_* chisel2v_*
rm -f tmp_*txt
rm -f output

docker kill $(docker ps -q)
