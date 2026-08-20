# Week 1 — Tooling

Started: <August 18 2026>

Template. Keep this honest rather than tidy — it is the raw material for
your README and for interview answers, and in week 6 you will not
remember any of it.

## What I built
Installed all tooling in Macbook. Python3, VS code, git, numby, pandas, matplotlib. Built a github repo. Created readme and practice functions.
Three required functions in python (moving average, standardized values and count consecutive above)

## What broke, and what fixed it


A venv broke because I renamed its parent folder, and the error message gave no hint why.I changed to the correct dir in a new terminal and reinstalled the entire package with numpy, pandas and matplotlib


My git repo was initialized one level above my project because i kept moving the project folder and adding other folders which also broke venv, which showed up as ../ prefixes in git status. Rebuilt the entire thing with Claude's help and pushed to github


mv folder/* silently skipped hidden files. used rm -rf to force remove all files and created the .gitignore folder. MacOS sees .(files) as invisible and they need to be manual revealed

two comparisons in one function (count_consectutive_above). The value test for threshold is strictly great and the streak test is at-least for n

## What I did not understand at first
the math behind the functions
how to use VS and python and terminal commands

## Decisions I made, and why

wrote functions first then leanred how to use python and then check.py. figured the functions were the hardest part and was right

## Interview gate — answered out loud, no notes

- [ ] What is a virtual environment and what problem does it solve?
- [ ] Difference between a list and a dict; when do you reach for each?
- [ ] What does `if __name__ == "__main__":` do and why is it there?

## Time spent

| Day | Hours | On what |
|---|---|---|
| Mon | | |
| Tue | |4|    functions
| Wed | |8|    python, VS code
| Thu | | |
| Fri | | |
| Sat | | |
