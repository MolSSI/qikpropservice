#!/usr/bin/env bash

TMPDIR=$(mktemp -d)

cp $1 $TMPDIR/entryfile

docker run --rm -v "$TMPDIR":/entry qikprop:latest

cp $TMPDIR/output.tar.gz .
