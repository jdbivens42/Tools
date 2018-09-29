#!/bin/bash

rm executor.iso

genisoimage -f -J -joliet-long -r -allow-lowercase -o executor.iso .
