#!/bin/bash
set -eu
RESULTDIR="./"
# Modify paths to your programs below as needed
GO1="./Go1/Go1.py"
GO2="./Go2/Go2.py"
TWOGTP=gogui-twogtp

run() {
echo Match with $NUGAMES games on board size $BOARDSIZE. Storing results in $RESULTDIR

mkdir -p $RESULTDIR
$TWOGTP -black "$GO1" -white "$GO2" \
-auto  -komi 0 -size $BOARDSIZE -games $NUGAMES \
-sgffile $RESULTDIR/game

$TWOGTP -analyze $RESULTDIR/game.dat -force
}

NUGAMES=10
BOARDSIZE=3
run