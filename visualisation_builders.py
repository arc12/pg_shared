
import plotly.graph_objects as go

def shap_force_plot(attr_index, attr_names, use_rec, title="Attribute Forces", x_axis_text="Probability/%", y_axis_text="Attribute"):
    """Use Plotly to make something similar to a Shap Waterfall plot using output from the Model Driven Synthesiser Jupyter notebook.

    :param attr_index: _description_
    :type attr_index: list(str)
    :param attr_names: _description_
    :type attr_names: list(str)
    :param use_rec: is a dict for a single prediction instance, with attribute and Shap values
    :type use_rec: dict
    :param title: _description_, defaults to "Attribute Forces"
    :type title: str|None, optional
    :param x_axis_text: _description_, defaults to "Probability/%"
    :type x_axis_text: str|None, optional
    :param y_axis_text: _description_, defaults to "Attribute"
    :type y_axis_text: str|None, optional
    :return: _description_
    :rtype: go.Figure
    """
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

    traces = [
            go.Bar(
                # each list gets an extra item inserted at the start, which is the "Base"
                base=bases[0:1] + bases,
                y=y_labels,
                x=[0] + steps,
                orientation="h",
                marker_color=["black"] +["deeppink" if ip else "dodgerblue" for ip in is_positive],
                text=[""] + bar_text,  # text of attribute value is aligned with the left end for -ve steps and right for +ve
                # text=[""] + [f"{t} >" if ip else f"< {t}" for ip, t in zip(is_positive, bar_text)],  # < and > markers might be confusing with numerical
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
        ]
    
    layout = {
            "title": {"text": title, "x": 0.5, "xref": "paper", "xanchor": "center"},
            "showlegend": False,
            "xaxis": {"title": x_axis_text, "fixedrange": True},
            "yaxis": {"title": y_axis_text, "fixedrange": True},
            "margin": go.layout.Margin(l=0, r=0, b=30, t=30)
        }
    
    return go.Figure(data=traces, layout=layout)