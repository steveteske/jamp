from jamp.plot import MetricPlot

from unittest.mock import patch, MagicMock

@patch("jamp.plot.plt")
def test_metric_plot(mock_plt, mock_metrics_df):
    mock_plt.subplots.return_value = (MagicMock(), MagicMock())
    mp = MetricPlot("bob")
    mp.plot(mock_metrics_df)