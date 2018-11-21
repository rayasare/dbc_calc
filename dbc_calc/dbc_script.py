#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
asare_proj.py
CHE 696 Project

Dynamic binding capacity calculator
Imports csv and reads loading data (column 1) and fraction breakthrough (column 2)
Fits a sigmoid curve (y = 1 / 1 + exp(-k(x-x0))) to the data, optimizes k and x0 and calculates R^2 fit parameter
If R^2 good, plots the sigmoid fit against the raw data, and displays the fit equation and R^2 value
"""

import sys
from argparse import ArgumentParser
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os

SUCCESS = 0
DEFAULT_DATA_FILE_NAME = 'tryagain.csv'
IO_ERROR = 1
INVALID_DATA = 2
SYNTAX_ERROR = 3


def warning(*objs):
    """Writes a message to stderr."""
    print("WARNING: ", *objs, file=sys.stderr)


def bad_fit(rsquared):
    """Prints an error message if the fit is poor."""
    print("WARNING: sigmoid fit is poor; r^2 = {}".format(round(rsquared, 2)))


def sigmoid(x, k, x0):
    """Defines the sigmoid function for fitting the data; unknown k and x0 values"""
    y = 1 / (1 + np.exp(-k*(x-x0)))
    return y


def data_analysis(data_array):
    """
    Splits the csv and feeds the sigmoid function
    Solves for sigmoid fit parameters k and x0; computes 10% DBC
    Computes R^2 for the sigmoid fit; rejects with warning if R^2 is less than 0.95

    Parameters
    ----------
    data_array : numpy array of dynamic binding capacity data (one line per fraction)

    Returns
    -------
    data_stats : numpy array
        (array with x data in column 0, y data in column 1, and k, x0, DBC_10%, and R^2 values in column 3)
    """
    xdata = data_array[:, 0]
    ydata = data_array[:, 1]
    p0 = [0.4, 70.0]

    popt, pcov = curve_fit(sigmoid, xdata, ydata, p0)

    ypredicted = 1 / (1 + np.exp(-popt[0]*(xdata-popt[1])))
    dbc_10p = (-np.log(9) / popt[0]) + popt[1]

    residcalc1 = (ydata - np.mean(ydata))**2
    residcalc2 = (ypredicted - np.mean(ydata))**2
    rsquared = np.sum(residcalc2) / np.sum(residcalc1)

    num_rows, num_columns = data_array.shape
    data_stats = np.zeros((num_rows, 3))

    data_stats[:, 0] = xdata
    data_stats[:, 1] = ydata
    data_stats[0, 2] = popt[0]
    data_stats[1, 2] = popt[1]
    data_stats[2, 2] = dbc_10p
    data_stats[3, 2] = rsquared

    return data_stats


def plot_stats(base_f_name, base_name, data_stats, resin_type, residence_time):
    """
    Makes a plot of the raw data overlay with the sigmoid fit

    Parameters
    resin_type: optional argument (string) detailing resin
    residence_time: optional argument (string) detailing residence time
    ----------
    base_f_name: str of base output name (without extension)
    base_name: name of original file (without extension)
    data_stats: numpy array (with xdata in column 0, ydata in column 1, and k, x0, DBC_10%, and R^2 values in column 3)

    Returns
    -------
    saves a png file of the plot with relevant information
    """

    xdata = data_stats[:, 0]
    ydata = data_stats[:, 1]

    x = np.linspace(-1, 200, 200)
    y = 1 / (1 + np.exp(-data_stats[0, 2]*(x-data_stats[1, 2])))

    plt.plot(xdata, ydata, 'o', label='raw_data')
    plt.plot(x, y, label='fit')
    plt.title('Dynamic Binding Capacity 10% Curve for {}'.format(base_name))
    plt.xlabel('Resin Loading (g/L_resin)')
    plt.ylabel('Fraction Breakthrough')
    plt.yticks(np.arange(0, 1.1, 0.1))
    plt.figtext(.5, .4, "Resin: {}".format(resin_type))
    plt.figtext(.5, .35, "Residence Time: {}".format(residence_time))
    plt.figtext(.5, .3, "DBC 10% = {}g/L".format(round(data_stats[2, 2], 1)))
    plt.figtext(.5, .25, "R^2 = {}".format(round(data_stats[3, 2], 3)))
    plt.figtext(.5, .2, r"$ y = \frac {1}{e^{-k(x-x0)}} $")
    plt.figtext(.62, .2, "(k = {}".format(round(data_stats[0, 2], 1)))
    plt.figtext(.72, .2, "x0 = {})".format(round(data_stats[1, 2], 1)))
    plt.legend(loc='best')
    # plt.show()

    out_name = base_f_name + ".png"
    plt.savefig(out_name)
    print("Wrote file: {}".format(out_name))


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = ArgumentParser(description='Reads in a csv (no header) fits a sigmoid to the data. '
                                        'There must be the same number of values in each row.')
    parser.add_argument("-c", "--csv_data_file", help="The location (directory and file name) of the csv file with "
                                                      "data to analyze",
                        default=DEFAULT_DATA_FILE_NAME)
    parser.add_argument("-r", "--resin_type", help="Input the resin type as a string (in quotes)",
                        default='No user input')
    parser.add_argument("-t", "--time_of_residence", help="Input the residence time with units as a string (in quotes)",
                        default='No user input')
    args = None
    try:
        args = parser.parse_args(argv)
        args.csv_data = np.loadtxt(fname=args.csv_data_file, delimiter=',')
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except ValueError as e:
        warning("Read invalid data:", e)
        parser.print_help()
        return args, INVALID_DATA

    return args, SUCCESS


def main(argv=None):
    args, ret = parse_cmdline(argv)
    if ret != SUCCESS:
        return ret
    data_stats = data_analysis(args.csv_data)

    if data_stats[3, 2] > 1.05 or data_stats[3, 2] < 0.95:
        badrsquared = data_stats[3, 2]
        return bad_fit(badrsquared)

    # get the name of the input file without the directory it is in, if one was specified
    base_out_fname = os.path.basename(args.csv_data_file)
    # get the first part of the file name (omit extension) and add the suffix
    base_out_fname2 = os.path.splitext(base_out_fname)[0] + '_stats'
    # add suffix and extension
    out_fname = base_out_fname2 + '.csv'
    np.savetxt(out_fname, data_stats, delimiter=',')
    print("Wrote file: {}".format(out_fname))

    # send the base_out_fname and data to a new function that will plot the data
    plot_stats(base_out_fname2, base_out_fname, data_stats, args.resin_type, args.time_of_residence)

    return SUCCESS  # success


if __name__ == "__main__":
    status = main()
    sys.exit(status)
