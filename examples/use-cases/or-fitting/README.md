# Fitting a straight line to an ambiguous data set
In this use case, we are concerned with fitting a straight line to ambiguous data. The data is of the form y = +/- a * x = b, meaning that for every x value, there are two y values. 
The likelihood is such that for a given x value, the straight line can pass either close to one or both of the y values. This is realized by using a smooth approximation to the minimum function, an idea borrowed from the concept of ambiguous distance restraints (ADR) in protein structure calculation from nuclear magnetic resonance (NMR) data (see the [paper](https://www.sciencedirect.com/science/article/abs/pii/S0022283684700532) by Michael Nilges).
The posterior distribution for the slope of the line is thus bimodal. 

You can create a data set and write it to `data.txt` by running
```bash
$ python make_data.py data.txt
```
which will also show a plot with the data.
Other than that, follow the [general use case instructions](../README.md).
