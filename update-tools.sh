#!/bin/bash
wget -O tools.zip https://github.com/jdbivens42/Tools/archive/master.zip
unzip tools.zip
chmod -R 700 Tools-master/*
chmod -R 400 Tools-master/ini/*
cp -r Tools-master/* .
rm -rf Tools-master/
