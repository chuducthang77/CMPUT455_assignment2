#!/bin/bash

# Script for running Go2 unit and basic functional tests

PROGRAM="go2.sh"
OUTPUTDIR="results_test_go2"
GO0DIR="../go0and1"

gogui-regress $PROGRAM -output $OUTPUTDIR $GO0DIR/test_go_base.tst
gogui-regress $PROGRAM -output $OUTPUTDIR $GO0DIR/test_simple_ko.tst
gogui-regress $PROGRAM -output $OUTPUTDIR $GO0DIR/test_suicide.tst
gogui-regress $PROGRAM -output $OUTPUTDIR test_go2.tst
