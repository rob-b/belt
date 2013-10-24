#!/bin/sh

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$BRANCH" = 'develop' -o "$BRANCH" = 'master' ]
then
    git stash -q --keep-index
    py.test
    result=$?
    git stash pop -q
    [ $result -ne 0 ] && exit 1
fi
exit 0
