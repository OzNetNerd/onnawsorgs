#!/bin/bash

cd onnawsorgs
PYTHONPATH=. pdoc --html . --force -o ../docs
mv ../docs/onnawsorgs/* ../docs
rmdir ../docs/onnawsorgs/