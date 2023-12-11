#!/bin/bash

REPO_NAME_LOCAL=$1
SYNERGY_PATTERN=eosc-synergy
IFCA_PATTERN=ifca-advanced-computing

[[ $# -ne 1 ]] && echo "Ignoring: bad arguments provided" && exit -1

case ${REPO_NAME_LOCAL,,} in
    *eosc-synergy*)
        find . -type f \( -name \*.md -o -name \*.rst -o -name \*.toml -o -name \*.html -o -name \*.cff -o -name Dockerfile \) -exec sed -i "s/${IFCA_PATTERN}\/FAIR_eva/${SYNERGY_PATTERN}\/FAIR_eva/gI" {} +
        ;;
    *ifca-advanced-computing*)
        find . -type f \( -name \*.md -o -name \*.rst -o -name \*.toml -o -name \*.html -o -name \*.cff -o -name Dockerfile \) -exec sed -i "s/${SYNERGY_PATTERN}\/FAIR_eva/${IFCA_PATTERN}\/FAIR_eva/gI" {} +
        ;;
    *) echo "No pattern matching found"
        ;;
esac
