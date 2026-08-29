# Week 2  - <Math>

Started: <August 21 2026>


## What I built
rk4 integrator with test functions

## What broke, and what fixed it

was using the wrong homebrew python which was bypassing venv. switched to correct version
learned to add if __name__ == "__main__" for test functions inside defining functions code (defininations are fine, actions need to be guarded)
learned that functions are case sensitive
global and local variables are not the same
using variables in a while and if loop that are local and not global
puting lists as values in np arrays


## What I did not understand at first
the math behind rk4 (rusty)
how to pass functions as vectors and arrays using numpy to represent the arrays to exectue across vectors
how to use if name == main
local and global variable differences
how to prompt user for numbers
how to include the convergence test inside of functions that use assert instead of print
how to print tables inside of loops
the difference between functions and loops
anything meant to be called by other code has to take its parameters as arguments not fish for them at the keyboard. layer print and functions. pure functions underneath and an optional interactive layer on top
how to write a print_tabel function

## Decisions I made, and why

wrote rk4 first in math then in pythons
wrote test function inside rk4 function
wrote code to test convergence and analytical solutions in seperate file that calls on the rk4 file
decided to make an interactive test file for some reason to test rk4


## Interview gate — answered out loud, no notes

- [ ] Why is RK4 fourth-order? What does "order" mean here?
- [ ] Your convergence test — why 16x and not 4x?
- [ ] What does "vectorized" mean, and why is a Python loop over 100,000
      numpy elements slower than the equivalent array expression?

## Verification log

<!-- Record the actual numbers from your three checks. You will quote
     these later, and "I verified it" is worth far less than
     "error dropped 15.8x when I halved the step". -->

| Check | Result |
|---|---|
| Analytic comparison, error at t=2 | |
| Convergence ratio (h=0.1 vs h=0.05) | |
| Oscillator energy drift over 20 periods | |



## Time spent

| Day | Hours | On what |
|---|---|---|
| Mon | | |
| Tue | |4|    functions - week1
| Wed | |8|    python, VS code - week1
| Thu | |8|    50% week1 + 50% week2
| Fri | |8|    rk4 functions and tests
| Sat | |4|

| Day | Hours | On what |
|---|---|---|
| Mon | |4|       writing rk4
| Tue | |4|       test functions + convergence
| Wed | |4|       test functions + convergence
| Thu | |2|       print functions and code cleanup
| Fri | | |
| Sat | | |