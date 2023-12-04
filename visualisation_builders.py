
import plotly.graph_objects as go

# use Plotly to make something similar to a Shap Waterfall plot using output from the Model Driven Synthesiser Jupyter notebook.
# use_rec is a dict for a single prediction instance, with attribute and Shap values
def shap_force_plot(attr_index, attr_names, use_rec, title="Attribute Forces", x_axis_text="Probability/%", y_axis_text="Attribute"):
    p = use_rec["shap_probs"]
    bases = [b * 100 for b in p[:-1]]
    steps = [100 * (p[i+1] - p[i]) for i in range(len(p) - 1)]
    is_positive = [s > 0 for s in steps]

    y_labels = ["Base"] + attr_names # use attribute names, not codes
    bar_text = [str(use_rec[f"{a}#value"]) for a in attr_index] # attribute values as names (not codes) or point numerics in range. NB no Base here

    # disconnected lines to be shown as arrows indicating how to read the plot
    arrow_steps_x = []
    arrow_steps_y = []
    for i in range(len(bases)):
        if i > 0:
            arrow_steps_x.append(None)
            arrow_steps_y.append(None)
        arrow_steps_x += [bases[i], bases[i]]
        arrow_steps_y += [y_labels[i], y_labels[i + 1]]

    fig = go.Figure(
        data=[
            go.Bar(
                # each list gets an extra item inserted at the start, which is the "Base"
                base=bases[0:1] + bases,
                y=y_labels,
                x=[0] + steps,
                orientation="h",
                marker_color=["black"] +["deeppink" if ip else "dodgerblue" for ip in is_positive],
                text=[""] + [f"{t} >" if ip else f"< {t}" for ip, t in zip(is_positive, bar_text)],
                hoverinfo="text", hovertext = [""] + [f"{s:+.1f}% => {b+s:.1f}%" for s, b in zip(steps, bases[:-1])]
            ),
            # base and final blobs
            go.Scatter(
                x=[bases[0], bases[-1] + steps[-1]],
                y=[y_labels[0], y_labels[-1]],
                mode="markers",
                marker={"color": "gray", "size": 10},
                hovertemplate="%{x:.1f}%"
            ),
            # step arrows
            go.Scatter(
                x=arrow_steps_x,
                y=arrow_steps_y,
                marker={"color": "black", "symbol": "arrow-up", "angleref": "previous", "size": 12},
                hoverinfo="skip"
            )
        ],
        layout={
            "title": title,
            "showlegend": False,
            "xaxis": {"title": x_axis_text, "fixedrange": True},
            "yaxis": {"title": y_axis_text, "fixedrange": True}})

    return fig