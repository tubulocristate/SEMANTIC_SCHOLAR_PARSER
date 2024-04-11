#!.env/bin/python

import sys

n = 2

guess = 100
last_bigger = 0
while True:
	if guess > n:
		last_bigger = guess
		guess //= 2
		if guess < n:
			break
	else:
		guess += guess//2
print(last_bigger)
lower, upper = guess, last_bigger
while not (upper - lower) == 1:
	present = ((upper + lower) // 2) < n
	print(present)
	if present:
		lower = (upper + lower) // 2
	else:
		upper = (upper + lower) // 2
	print(lower, upper)
