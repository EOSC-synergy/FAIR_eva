#!/bin/bash
exec < /dev/tty

# Get the current branch name
branch_name=$(git branch | grep "*" | sed "s/\* //")

# Get the name of the branch that was just merged
reflog_message=$(git reflog -1)
merged_branch_name=$(echo $reflog_message | cut -d" " -f 4 | sed "s/://")

echo "-------------------"
echo "Current branch: $branch_name"
echo "Merged branch: $merged_branch_name"
echo "Reflog message: $reflog_message"
echo "-------------------"

# if the merged branch was master - don't do anything
if [[ $merged_branch_name != "_repo-sync" ]]; then
    echo "Merged branch is not <_repo-sync>, ignoring.."
    exit 0
fi

# Modify references to upstream repo with the current repo
find . -type f \( -name \*.md -o -name \*.rst -o -name \*.toml -o -name \*.html \) -exec sed -i 's/IFCA-Advanced-Computing\/FAIR_eva/eosc-synergy\/FAIR_eva/g' {} +
modified_files=$(git status --porcelain)
echo "The following list of files where modified:\n\n${modified_files}"
git add .
git commit -m "Update references to eosc-synergy/FAIR_eva"
git push origin HEAD
echo "File changes pushed to ${branch_name}"
