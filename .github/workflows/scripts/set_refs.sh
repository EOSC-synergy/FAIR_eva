#!/bin/bash

BRANCH_NAME=$1
ORG_LOCAL=eosc-synergy
ORG_UPSTREAM=IFCA-Advanced-Computing

[[ -z $BRANCH_NAME ]] && echo "Ignoring: no branch name provided" && exit -1

if [[ $BRANCH_NAME == "merge/repo-sync" ]]; then
    echo "Setting references to eosc-synergy"
    find . -type f \( -name \*.md -o -name \*.rst -o -name \*.toml -o -name \*.html -o -name \*.cff \) -exec sed -i "s/${ORG_UPSTREAM}\/FAIR_eva/${ORG_LOCAL}\/FAIR_eva/g" {} +
elif [[ $BRANCH_NAME == "merge/upstream" ]]; then
    echo "Setting references to IFCA-Advanced-Computing"
    find . -type f \( -name \*.md -o -name \*.rst -o -name \*.toml -o -name \*.html -o -name \*.cff \) -exec sed -i "s/${ORG_LOCAL}\/FAIR_eva/${ORG_UPSTREAM}\/FAIR_eva/g" {} +
else
    echo "Ignoring: branch name <$BRANCH_NAME> is not in [merge/repo-sync, merge/upstream]"
fi
