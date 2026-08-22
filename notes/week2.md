# Week 2  - <Math>

Started: <August 21 2026>


## What I built
rk4 integrator with test functions

## What broke, and what fixed it

was using the wrong homebrew python which was bypassing venv. switched to correct version
learned to add if __name__ == "__main__" for test functions inside defining functions code (defininations are fine, actions need to be guarded)
learned that functions are case sensitive

## What I did not understand at first
the math behind rk4 (rusty)
how to pass functions as vectors and arrays using numpy to represent the arrays to exectue across vectors

## Decisions I made, and why

wrote rk4 first in math then in pythons
wrote test function inside rk4 function


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
| Sat | | |

| Day | Hours | On what |
|---|---|---|
| Mon | | |
| Tue | | |
| Wed | | |
| Thu | | |
| Fri | | |
| Sat | | |