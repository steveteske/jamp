
import argparse

import pandas as pd

from jamp.plot import MetricPlot


class ExecutePlot:

    def __init__(self):
        self._args = self.parse_args()
        self._plotter = MetricPlot(self._args.file,
                                   "agile_metrics.png")
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Build Program in Jira')
        parser.add_argument('--file', type=str, required=True,
                            help='file name for excel input')
        parser.add_argument('--image', type=str, required=True,
                            help='file name for image output')

        return parser.parse_args()

    def read(self):
        return pd.read_csv(self._args.file)

    def run(self):
        df = self.read()
        self._plotter.plot(df)

if __name__ == "__main__":
    ExecutePlot().run()
