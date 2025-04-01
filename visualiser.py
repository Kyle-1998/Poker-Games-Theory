import plotly.graph_objects as go
from plotly.subplots import make_subplots

DEFAULT_COLORS = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

def plot_metrics_subplots(metrics_data, config):
    """
    Creates a Plotly figure with multiple subplots based on the given configuration.
    
    The configuration should be a dictionary with:
      - "chart_title": overall chart title.
      - "subplots": a list of subplots, where each subplot is a dictionary with:
            "title": subplot title,
            "series": a list of dictionaries, each containing:
                 "metric": key from metrics_data,
                 "name": display name for the series,
                 "color": (optional) color for the series.
    
    Parameters:
        metrics_data (list of dict): List of metric dictionaries, each with an 'iteration' key.
        config (dict): Plot configuration dictionary.
    
    Returns:
        fig: A Plotly figure object.
    """
    subplots = config.get("subplots", [])
    chart_title = config.get("chart_title", "Evolution of Metrics")
    num_subplots = len(subplots)
    
    # Create vertically stacked subplots with a shared x-axis.
    fig = make_subplots(
        rows=num_subplots, cols=1, shared_xaxes=True,
        subplot_titles=[sp.get("title", "") for sp in subplots]
    )
    
    iterations = [d['iteration'] for d in metrics_data]
    
    for idx, subplot in enumerate(subplots, start=1):
        series_list = subplot.get("series", [])
        for s_idx, series in enumerate(series_list):
            metric_key = series.get("metric")
            display_name = series.get("name", metric_key)
            color = series.get("color")
            
            if color is None:
                color = DEFAULT_COLORS[s_idx % len(DEFAULT_COLORS)]
            y_values = [d.get(metric_key) for d in metrics_data]
            fig.add_trace(
                go.Scatter(
                    x=iterations,
                    y=y_values,
                    mode='lines+markers',
                    name=display_name,
                    line=dict(color=color),
                    marker=dict(size=6)
                ),
                row=idx, col=1
            )
    
    fig.update_layout(title=chart_title, template="plotly_dark")
    return fig
