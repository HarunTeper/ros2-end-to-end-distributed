"""This is the main file of the program."""

import os

from system import System
from optimization import Optimization


def main():
    """Start main function."""

    configuration = 'indy.yaml'

    system = System('system_configurations/' + configuration)

    print('Running optimization...')
    Optimization(system)

if __name__ == '__main__':
    main()
