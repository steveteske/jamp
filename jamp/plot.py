import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from io import StringIO

class MetricPlot:

    def __init__(self, image_file: str, show=False):
        self._image_filename = image_file
        self._show = show

    def plot(self, df: pd.DataFrame) -> None:
        print(df)
        # Not sure why I cannot just drop the first column.
        # ...When I read from CSV it works, but not direct
        # ...from DataFrame.
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        df = pd.read_csv(buffer)
        print(df)
        pivot = df.pivot_table(
            values=['Story Points Committed', 'Story Points Completed', '% Complete'],
            index=['Sprint'],
            aggfunc={'Story Points Committed': np.sum,
                     'Story Points Completed': np.sum,
                     '% Complete': np.mean})

        print(pivot)

        pos = pivot.index
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()

        ax1.bar(pos, pivot['Story Points Committed'], color='grey', align='edge', width=-0.4)
        ax1.bar(pos, pivot['Story Points Completed'], color='green', align='edge', width=0.4)
        ax1.set_ylabel('Story Points')
        ax1.set_xlabel('Sprints')

        ax2.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        style = dict(linestyle=':',
                     color='purple',
                     markersize=30,
                     mfc="C0",
                     mec="C0")

        horz = 10
        vert = 1
        verts = [[-1 * horz, -1 * vert],
                 [1 * horz, -1 * vert],
                 [1 * horz, 1 * vert],
                 [-1 * horz, 1 * vert],
                 [-1 * horz, -1 * vert]]

        for index, point in enumerate(pivot['% Complete']):
            x = pos[index]
            y = point
            print(index, x, y)
            ax2.scatter(x, y, s=100, c='purple', marker=verts)
            ax2.annotate("{:.0%}".format(y), (x, y))
        ax2.plot(pos, pivot['% Complete'], color='purple')
        ax2.set_ylabel('% Complete')
        ax2.set_ylim(bottom=0)

        golden_ratio = 1.618
        vert = 8
        fig.set_size_inches(vert * golden_ratio, vert)

        plt.savefig(self._image_filename, dpi=100.0, format='png')
        if (self._show):
            plt.show()
