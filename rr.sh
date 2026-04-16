#!/bin/bash
jq '
    (group_by(.src) | map(.[0])) as $one_each |
    ($one_each | map(.id)) as $seen |
    ($one_each + ([.[] | select(.id as $id | $seen | index($id) | not)] | .[0:7])) |
    .[0:10]
' data/usfs/usfs_catalog.json
