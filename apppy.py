from io import StringIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import (
    Dash,
    Input,
    Output,
    State,
    callback,
    dash_table,
    dcc,
    html,
)

from data_reader import load_sales_data


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

df = load_sales_data()


# ---------------------------------------------------------
# DASH APPLICATION
# ---------------------------------------------------------

app = Dash(
    __name__,
    title="Philippines SFE Dashboard",
    suppress_callback_exceptions=True,
)

server = app.server


# ---------------------------------------------------------
# COLOURS
# ---------------------------------------------------------

COLORS = {
    "navy": "#153B5B",
    "blue": "#0B75A5",
    "light_blue": "#E8F4FA",
    "teal": "#00A6A6",
    "green": "#2E8B57",
    "orange": "#F39C12",
    "red": "#C0392B",
    "purple": "#6C5CE7",
    "grey": "#667085",
    "light_grey": "#F4F7FB",
    "white": "#FFFFFF",
}


CHART_COLORS = [
    "#0B75A5",
    "#00A6A6",
    "#6C5CE7",
    "#F39C12",
    "#2E8B57",
    "#C0392B",
]


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def make_options(data, column):
    """
    Creates dropdown options from one dataframe column.
    """

    values = sorted(
        data[column]
        .dropna()
        .astype(str)
        .unique()
    )

    return [
        {
            "label": value,
            "value": value,
        }
        for value in values
    ]


def format_php(value):
    """
    Formats Philippine peso values.
    """

    if value >= 1_000_000_000:
        return f"PHP {value / 1_000_000_000:.2f} B"

    if value >= 1_000_000:
        return f"PHP {value / 1_000_000:.2f} M"

    if value >= 1_000:
        return f"PHP {value / 1_000:.1f} K"

    return f"PHP {value:,.0f}"


def create_kpi_card(
    title,
    component_id,
    subtitle,
    accent_colour,
):
    """
    Creates an individual KPI card.
    """

    return html.Div(
        [
            html.Div(
                title,
                style={
                    "fontSize": "11px",
                    "fontWeight": "700",
                    "letterSpacing": "0.7px",
                    "color": COLORS["grey"],
                },
            ),
            html.Div(
                id=component_id,
                children="-",
                style={
                    "fontSize": "27px",
                    "fontWeight": "800",
                    "color": accent_colour,
                    "marginTop": "8px",
                },
            ),
            html.Div(
                subtitle,
                style={
                    "fontSize": "11px",
                    "color": "#98A2B3",
                    "marginTop": "7px",
                },
            ),
        ],
        style={
            "backgroundColor": COLORS["white"],
            "padding": "18px",
            "borderRadius": "15px",
            "borderTop": f"4px solid {accent_colour}",
            "boxShadow": "0 4px 15px rgba(16, 24, 40, 0.08)",
            "minHeight": "105px",
        },
    )


def standard_chart_layout(
    figure,
    height=430,
):
    """
    Applies a common visual style to Plotly charts.
    """

    figure.update_layout(
        template="plotly_white",
        height=height,
        margin={
            "l": 35,
            "r": 25,
            "t": 65,
            "b": 40,
        },
        font={
            "family": "Arial",
            "color": "#344054",
        },
        title={
            "font": {
                "size": 18,
                "color": COLORS["navy"],
            },
            "x": 0.02,
        },
        hoverlabel={
            "bgcolor": COLORS["navy"],
            "font_color": COLORS["white"],
        },
        paper_bgcolor=COLORS["white"],
        plot_bgcolor=COLORS["white"],
        transition={
            "duration": 500,
            "easing": "cubic-in-out",
        },
    )

    return figure


def empty_figure(message):
    """
    Creates a clean empty chart when filters return no data.
    """

    figure = go.Figure()

    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={
            "size": 18,
            "color": COLORS["grey"],
        },
    )

    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)

    return standard_chart_layout(figure)


# ---------------------------------------------------------
# FILTER OPTIONS
# ---------------------------------------------------------

week_options = [
    {
        "label": "All weeks",
        "value": "ALL",
    }
]

for reporting_week in sorted(
    df["Week_Start"].dropna().unique()
):
    reporting_week = pd.Timestamp(reporting_week)

    week_options.append(
        {
            "label": reporting_week.strftime(
                "%d %b %Y"
            ),
            "value": reporting_week.strftime(
                "%Y-%m-%d"
            ),
        }
    )


# ---------------------------------------------------------
# DASHBOARD LAYOUT
# ---------------------------------------------------------

app.layout = html.Div(
    [
        # Header
        html.Div(
            [
                html.Div(
                    [
                        html.H1(
                            "Philippines SFE Tracking Dashboard",
                            style={
                                "margin": "0",
                                "fontSize": "30px",
                            },
                        ),
                        html.P(
                            (
                                "Synthetic weekly sales force effectiveness "
                                "data | 150 representatives"
                            ),
                            style={
                                "marginTop": "7px",
                                "marginBottom": "0",
                                "fontSize": "14px",
                            },
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Div(
                            "Last refreshed",
                            style={
                                "fontSize": "10px",
                                "opacity": "0.8",
                            },
                        ),
                        html.Div(
                            id="refresh-time",
                            children="Application started",
                            style={
                                "fontSize": "13px",
                                "fontWeight": "700",
                                "marginTop": "4px",
                            },
                        ),
                        html.Button(
                            "Refresh Excel data",
                            id="refresh-button",
                            n_clicks=0,
                            style={
                                "marginTop": "10px",
                                "padding": "10px 15px",
                                "border": "none",
                                "borderRadius": "9px",
                                "backgroundColor": COLORS["white"],
                                "color": COLORS["navy"],
                                "fontWeight": "700",
                                "cursor": "pointer",
                            },
                        ),
                    ],
                    style={
                        "textAlign": "right",
                    },
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "24px 28px",
                "borderRadius": "17px",
                "color": COLORS["white"],
                "background": (
                    "linear-gradient(120deg, "
                    "#153B5B 0%, #0B75A5 100%)"
                ),
                "boxShadow": (
                    "0 8px 24px "
                    "rgba(21, 59, 91, 0.22)"
                ),
            },
        ),

        # Filters
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "REPORTING WEEK",
                            className="filter-label",
                        ),
                        dcc.Dropdown(
                            id="week-filter",
                            options=week_options,
                            value="ALL",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label(
                            "REGION",
                            className="filter-label",
                        ),
                        dcc.Dropdown(
                            id="region-filter",
                            options=(
                                [
                                    {
                                        "label": "All regions",
                                        "value": "ALL",
                                    }
                                ]
                                + make_options(
                                    df,
                                    "Region",
                                )
                            ),
                            value="ALL",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label(
                            "INDICATION",
                            className="filter-label",
                        ),
                        dcc.Dropdown(
                            id="indication-filter",
                            options=(
                                [
                                    {
                                        "label": "All indications",
                                        "value": "ALL",
                                    }
                                ]
                                + make_options(
                                    df,
                                    "Indication",
                                )
                            ),
                            value="ALL",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label(
                            "TEAM",
                            className="filter-label",
                        ),
                        dcc.Dropdown(
                            id="team-filter",
                            options=(
                                [
                                    {
                                        "label": "All teams",
                                        "value": "ALL",
                                    }
                                ]
                                + make_options(
                                    df,
                                    "Team",
                                )
                            ),
                            value="ALL",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label(
                            "CHANNEL",
                            className="filter-label",
                        ),
                        dcc.Dropdown(
                            id="channel-filter",
                            options=(
                                [
                                    {
                                        "label": "All channels",
                                        "value": "ALL",
                                    }
                                ]
                                + make_options(
                                    df,
                                    "Channel",
                                )
                            ),
                            value="ALL",
                            clearable=False,
                        ),
                    ]
                ),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": (
                    "repeat(5, minmax(180px, 1fr))"
                ),
                "gap": "14px",
                "padding": "18px",
                "marginTop": "16px",
                "backgroundColor": COLORS["white"],
                "borderRadius": "15px",
                "boxShadow": (
                    "0 4px 15px "
                    "rgba(16, 24, 40, 0.07)"
                ),
            },
        ),

        # KPI cards
        html.Div(
            [
                create_kpi_card(
                    "NET SALES",
                    "net-sales-kpi",
                    "Sales value after returns",
                    COLORS["blue"],
                ),
                create_kpi_card(
                    "TARGET ATTAINMENT",
                    "attainment-kpi",
                    "Gross units divided by unit target",
                    COLORS["green"],
                ),
                create_kpi_card(
                    "PRODUCTIVE CALL RATE",
                    "productive-rate-kpi",
                    "Productive calls divided by total calls",
                    COLORS["purple"],
                ),
                create_kpi_card(
                    "HCP REACH",
                    "hcp-reach-kpi",
                    "Recorded HCP interactions",
                    COLORS["orange"],
                ),
                create_kpi_card(
                    "DATA COMPLETENESS",
                    "completeness-kpi",
                    "Average data quality score",
                    COLORS["teal"],
                ),
                create_kpi_card(
                    "RETURN RATE",
                    "return-rate-kpi",
                    "Returned units divided by gross units",
                    COLORS["red"],
                ),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": (
                    "repeat(6, minmax(160px, 1fr))"
                ),
                "gap": "14px",
                "marginTop": "16px",
            },
        ),

        # First chart row
        html.Div(
            [
                html.Div(
                    dcc.Graph(
                        id="weekly-sales-chart",
                        config={
                            "displaylogo": False,
                            "responsive": True,
                        },
                    ),
                    className="chart-panel",
                ),
                html.Div(
                    dcc.Graph(
                        id="animated-map-chart",
                        config={
                            "displaylogo": False,
                            "responsive": True,
                        },
                    ),
                    className="chart-panel",
                ),
            ],
            className="two-column-grid",
        ),

        # Second chart row
        html.Div(
            [
                html.Div(
                    dcc.Graph(
                        id="indication-sales-chart",
                        config={
                            "displaylogo": False,
                            "responsive": True,
                        },
                    ),
                    className="chart-panel",
                ),
                html.Div(
                    dcc.Graph(
                        id="representative-ranking-chart",
                        config={
                            "displaylogo": False,
                            "responsive": True,
                        },
                    ),
                    className="chart-panel",
                ),
            ],
            className="two-column-grid",
        ),

        # Third chart row
        html.Div(
            [
                html.Div(
                    dcc.Graph(
                        id="target-gauge-chart",
                        config={
                            "displaylogo": False,
                            "responsive": True,
                        },
                    ),
                    className="chart-panel",
                ),
                html.Div(
                    dcc.Graph(
                        id="activity-scatter-chart",
                        config={
                            "displaylogo": False,
                            "responsive": True,
                        },
                    ),
                    className="chart-panel",
                ),
            ],
            className="two-column-grid",
        ),

        # Representative table
        html.Div(
            [
                html.H3(
                    "Representative Performance Detail",
                    style={
                        "color": COLORS["navy"],
                        "marginTop": "0",
                    },
                ),
                dash_table.DataTable(
                    id="representative-table",
                    page_size=15,
                    sort_action="native",
                    filter_action="native",
                    export_format="xlsx",
                    export_headers="display",
                    style_table={
                        "overflowX": "auto",
                    },
                    style_header={
                        "backgroundColor": COLORS["navy"],
                        "color": COLORS["white"],
                        "fontWeight": "700",
                        "padding": "11px",
                        "border": "none",
                    },
                    style_cell={
                        "padding": "9px",
                        "textAlign": "left",
                        "fontFamily": "Arial",
                        "fontSize": "12px",
                        "border": (
                            "1px solid #EAECF0"
                        ),
                    },
                    style_data_conditional=[
                        {
                            "if": {
                                "filter_query": (
                                    "{Target Attainment %} >= 100"
                                ),
                                "column_id": (
                                    "Target Attainment %"
                                ),
                            },
                            "backgroundColor": "#D1FADF",
                            "color": "#05603A",
                            "fontWeight": "700",
                        },
                        {
                            "if": {
                                "filter_query": (
                                    "{Target Attainment %} < 80"
                                ),
                                "column_id": (
                                    "Target Attainment %"
                                ),
                            },
                            "backgroundColor": "#FEE4E2",
                            "color": "#B42318",
                            "fontWeight": "700",
                        },
                    ],
                ),
            ],
            style={
                "marginTop": "16px",
                "backgroundColor": COLORS["white"],
                "padding": "20px",
                "borderRadius": "15px",
                "boxShadow": (
                    "0 4px 15px "
                    "rgba(16, 24, 40, 0.07)"
                ),
            },
        ),

        # Data storage
        dcc.Store(
            id="sales-data-store"
        ),

        dcc.Interval(
            id="animation-refresh",
            interval=15 * 60 * 1000,
            n_intervals=0,
        ),
    ],
    style={
        "backgroundColor": COLORS["light_grey"],
        "minHeight": "100vh",
        "padding": "16px",
        "fontFamily": "Arial",
    },
)


# ---------------------------------------------------------
# DASHBOARD CSS
# ---------------------------------------------------------

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}

        <style>
            body {
                margin: 0;
                background-color: #F4F7FB;
            }

            .filter-label {
                display: block;
                font-family: Arial;
                font-size: 10px;
                font-weight: 700;
                color: #475467;
                margin-bottom: 7px;
                letter-spacing: 0.5px;
            }

            .two-column-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin-top: 16px;
            }

            .chart-panel {
                background-color: white;
                border-radius: 15px;
                padding: 5px;
                box-shadow:
                    0 4px 15px rgba(16, 24, 40, 0.07);
            }

            @media screen and (max-width: 1100px) {
                .two-column-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>

    <body>
        {%app_entry%}

        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


# ---------------------------------------------------------
# REFRESH CALLBACK
# ---------------------------------------------------------

@callback(
    Output(
        "sales-data-store",
        "data",
    ),
    Output(
        "refresh-time",
        "children",
    ),
    Input(
        "refresh-button",
        "n_clicks",
    ),
    Input(
        "animation-refresh",
        "n_intervals",
    ),
)
def refresh_data(
    refresh_clicks,
    interval_count,
):
    """
    Reloads the Excel workbook when the refresh button is clicked
    or when the automatic interval runs.
    """

    refreshed_df = load_sales_data()

    refresh_time = pd.Timestamp.now().strftime(
        "%d %b %Y, %H:%M:%S"
    )

    data_json = refreshed_df.to_json(
        date_format="iso",
        orient="split",
    )

    return data_json, refresh_time


# ---------------------------------------------------------
# MAIN DASHBOARD CALLBACK
# ---------------------------------------------------------

@callback(
    Output(
        "net-sales-kpi",
        "children",
    ),
    Output(
        "attainment-kpi",
        "children",
    ),
    Output(
        "productive-rate-kpi",
        "children",
    ),
    Output(
        "hcp-reach-kpi",
        "children",
    ),
    Output(
        "completeness-kpi",
        "children",
    ),
    Output(
        "return-rate-kpi",
        "children",
    ),
    Output(
        "weekly-sales-chart",
        "figure",
    ),
    Output(
        "animated-map-chart",
        "figure",
    ),
    Output(
        "indication-sales-chart",
        "figure",
    ),
    Output(
        "representative-ranking-chart",
        "figure",
    ),
    Output(
        "target-gauge-chart",
        "figure",
    ),
    Output(
        "activity-scatter-chart",
        "figure",
    ),
    Output(
        "representative-table",
        "data",
    ),
    Output(
        "representative-table",
        "columns",
    ),
    Input(
        "sales-data-store",
        "data",
    ),
    Input(
        "week-filter",
        "value",
    ),
    Input(
        "region-filter",
        "value",
    ),
    Input(
        "indication-filter",
        "value",
    ),
    Input(
        "team-filter",
        "value",
    ),
    Input(
        "channel-filter",
        "value",
    ),
)
def update_dashboard(
    stored_data,
    selected_week,
    selected_region,
    selected_indication,
    selected_team,
    selected_channel,
):
    """
    Filters the data and updates all dashboard components.
    """

    if stored_data:
        dashboard_df = pd.read_json(
            StringIO(stored_data),
            orient="split",
        )

        dashboard_df["Week_Start"] = pd.to_datetime(
            dashboard_df["Week_Start"]
        )

    else:
        dashboard_df = df.copy()

    # Apply filters
    if selected_week != "ALL":

        dashboard_df = dashboard_df[
            dashboard_df["Week_Start"]
            == pd.to_datetime(selected_week)
        ]

    if selected_region != "ALL":

        dashboard_df = dashboard_df[
            dashboard_df["Region"]
            == selected_region
        ]

    if selected_indication != "ALL":

        dashboard_df = dashboard_df[
            dashboard_df["Indication"]
            == selected_indication
        ]

    if selected_team != "ALL":

        dashboard_df = dashboard_df[
            dashboard_df["Team"]
            == selected_team
        ]

    if selected_channel != "ALL":

        dashboard_df = dashboard_df[
            dashboard_df["Channel"]
            == selected_channel
        ]

    # No-data handling
    if dashboard_df.empty:

        empty = empty_figure(
            "No data available for the selected filters"
        )

        return (
            "PHP 0",
            "0.0%",
            "0.0%",
            "0",
            "0.0%",
            "0.0%",
            empty,
            empty,
            empty,
            empty,
            empty,
            empty,
            [],
            [],
        )

    # -----------------------------------------------------
    # KPI CALCULATIONS
    # -----------------------------------------------------

    total_sales = dashboard_df[
        "Net_Sales_PHP"
    ].sum()

    total_units = dashboard_df[
        "Gross_Units"
    ].sum()

    total_target = dashboard_df[
        "Unit_Target"
    ].sum()

    total_calls = dashboard_df[
        "Total_Calls"
    ].sum()

    productive_calls = dashboard_df[
        "Productive_Calls"
    ].sum()

    total_hcp_reach = dashboard_df[
        "Unique_HCPs"
    ].sum()

    average_completeness = dashboard_df[
        "Data_Completeness_Pct"
    ].mean()

    returned_units = dashboard_df[
        "Returns"
    ].sum()

    target_attainment = (
        total_units / total_target * 100
        if total_target > 0
        else 0
    )

    productive_call_rate = (
        productive_calls / total_calls * 100
        if total_calls > 0
        else 0
    )

    return_rate = (
        returned_units / total_units * 100
        if total_units > 0
        else 0
    )

    # -----------------------------------------------------
    # WEEKLY SALES TREND
    # -----------------------------------------------------

    weekly_sales = (
        dashboard_df.groupby(
            [
                "Week_Start",
                "Indication",
            ],
            as_index=False,
        )
        .agg(
            Net_Sales_PHP=(
                "Net_Sales_PHP",
                "sum",
            )
        )
    )

    weekly_sales_chart = px.line(
        weekly_sales,
        x="Week_Start",
        y="Net_Sales_PHP",
        color="Indication",
        markers=True,
        title="Weekly Sales Performance",
        color_discrete_sequence=CHART_COLORS,
    )

    weekly_sales_chart.update_traces(
        line={
            "width": 3,
        },
        marker={
            "size": 8,
        },
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "Week: %{x|%d %b %Y}<br>"
            "Sales: PHP %{y:,.0f}"
            "<extra></extra>"
        ),
    )

    weekly_sales_chart.update_yaxes(
        tickprefix="PHP ",
        tickformat="~s",
        gridcolor="#EAECF0",
    )

    weekly_sales_chart.update_xaxes(
        gridcolor="#F2F4F7",
    )

    weekly_sales_chart = standard_chart_layout(
        weekly_sales_chart
    )

    # -----------------------------------------------------
    # ANIMATED GEOGRAPHIC MAP
    # -----------------------------------------------------

    map_data = (
        dashboard_df.groupby(
            [
                "Week_No",
                "Week_Start",
                "Region",
                "City",
                "Latitude",
                "Longitude",
            ],
            as_index=False,
        )
        .agg(
            Net_Sales_PHP=(
                "Net_Sales_PHP",
                "sum",
            ),
            Unique_HCPs=(
                "Unique_HCPs",
                "sum",
            ),
            Gross_Units=(
                "Gross_Units",
                "sum",
            ),
        )
    )

    map_data["Animation_Week"] = (
        map_data["Week_No"]
        .astype(int)
        .astype(str)
        .str.zfill(2)
    )

    animated_map_chart = px.scatter_map(
        map_data,
        lat="Latitude",
        lon="Longitude",
        size="Net_Sales_PHP",
        color="Region",
        hover_name="City",
        hover_data={
            "Net_Sales_PHP": ":,.0f",
            "Unique_HCPs": ":,.0f",
            "Gross_Units": ":,.0f",
            "Latitude": False,
            "Longitude": False,
            "Animation_Week": False,
        },
        animation_frame="Animation_Week",
        size_max=42,
        zoom=4.2,
        center={
            "lat": 12.4,
            "lon": 122.1,
        },
        map_style="open-street-map",
        title="Animated Geographic Sales Performance",
        color_discrete_sequence=CHART_COLORS,
    )

    animated_map_chart.update_layout(
        height=520,
        margin={
            "l": 0,
            "r": 0,
            "t": 65,
            "b": 0,
        },
        title={
            "font": {
                "size": 18,
                "color": COLORS["navy"],
            },
            "x": 0.02,
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 0.01,
            "xanchor": "left",
            "x": 0.01,
            "bgcolor": (
                "rgba(255,255,255,0.80)"
            ),
        },
        transition={
            "duration": 600,
        },
    )

    # -----------------------------------------------------
    # INDICATION SALES
    # -----------------------------------------------------

    indication_sales = (
        dashboard_df.groupby(
            "Indication",
            as_index=False,
        )
        .agg(
            Net_Sales_PHP=(
                "Net_Sales_PHP",
                "sum",
            ),
            Gross_Units=(
                "Gross_Units",
                "sum",
            ),
        )
        .sort_values(
            "Net_Sales_PHP",
            ascending=True,
        )
    )

    indication_sales_chart = px.bar(
        indication_sales,
        x="Net_Sales_PHP",
        y="Indication",
        orientation="h",
        color="Net_Sales_PHP",
        color_continuous_scale=[
            "#D9F0F7",
            "#0B75A5",
            "#153B5B",
        ],
        text="Net_Sales_PHP",
        title="Sales Contribution by Indication",
    )

    indication_sales_chart.update_traces(
        texttemplate="PHP %{text:,.0f}",
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Sales: PHP %{x:,.0f}"
            "<extra></extra>"
        ),
    )

    indication_sales_chart.update_layout(
        coloraxis_showscale=False,
    )

    indication_sales_chart.update_xaxes(
        tickprefix="PHP ",
        tickformat="~s",
        gridcolor="#EAECF0",
    )

    indication_sales_chart = standard_chart_layout(
        indication_sales_chart
    )

    # -----------------------------------------------------
    # REPRESENTATIVE SUMMARY
    # -----------------------------------------------------

    representative_data = (
        dashboard_df.groupby(
            [
                "Rep_ID",
                "Rep_Name",
                "Team",
                "Region",
            ],
            as_index=False,
        )
        .agg(
            Net_Sales_PHP=(
                "Net_Sales_PHP",
                "sum",
            ),
            Gross_Units=(
                "Gross_Units",
                "sum",
            ),
            Unit_Target=(
                "Unit_Target",
                "sum",
            ),
            Total_Calls=(
                "Total_Calls",
                "sum",
            ),
            Productive_Calls=(
                "Productive_Calls",
                "sum",
            ),
            Unique_HCPs=(
                "Unique_HCPs",
                "sum",
            ),
            Data_Completeness_Pct=(
                "Data_Completeness_Pct",
                "mean",
            ),
        )
    )

    representative_data[
        "Target_Attainment_Pct"
    ] = (
        representative_data["Gross_Units"]
        / representative_data[
            "Unit_Target"
        ].replace(0, pd.NA)
        * 100
    ).fillna(0)

    representative_data[
        "Productive_Call_Rate_Pct"
    ] = (
        representative_data["Productive_Calls"]
        / representative_data[
            "Total_Calls"
        ].replace(0, pd.NA)
        * 100
    ).fillna(0)

    # -----------------------------------------------------
    # TOP REPRESENTATIVES
    # -----------------------------------------------------

    top_representatives = (
        representative_data.nlargest(
            15,
            "Net_Sales_PHP",
        )
        .sort_values(
            "Net_Sales_PHP",
            ascending=True,
        )
    )

    representative_ranking_chart = px.bar(
        top_representatives,
        x="Net_Sales_PHP",
        y="Rep_Name",
        orientation="h",
        color="Target_Attainment_Pct",
        color_continuous_scale=[
            [0, "#F97066"],
            [0.5, "#FDB022"],
            [1, "#12B76A"],
        ],
        text="Net_Sales_PHP",
        title="Top 15 Sales Representatives",
        hover_data={
            "Team": True,
            "Region": True,
            "Target_Attainment_Pct": ":.1f",
            "Net_Sales_PHP": ":,.0f",
        },
    )

    representative_ranking_chart.update_traces(
        texttemplate="PHP %{text:,.0f}",
        textposition="outside",
    )

    representative_ranking_chart.update_xaxes(
        tickprefix="PHP ",
        tickformat="~s",
        gridcolor="#EAECF0",
    )

    representative_ranking_chart = standard_chart_layout(
        representative_ranking_chart,
        height=500,
    )

    # -----------------------------------------------------
    # TARGET ATTAINMENT GAUGE
    # -----------------------------------------------------

    target_gauge_chart = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=target_attainment,
            number={
                "suffix": "%",
                "font": {
                    "size": 45,
                    "color": COLORS["navy"],
                },
            },
            delta={
                "reference": 100,
                "relative": False,
                "valueformat": ".1f",
            },
            title={
                "text": (
                    "Overall Target Attainment"
                    "<br>"
                    "<span style='font-size:12px;"
                    "color:#667085'>"
                    "Reference target: 100%"
                    "</span>"
                )
            },
            gauge={
                "axis": {
                    "range": [
                        0,
                        max(
                            130,
                            target_attainment + 10,
                        ),
                    ],
                    "tickwidth": 1,
                },
                "bar": {
                    "color": COLORS["blue"],
                    "thickness": 0.32,
                },
                "bgcolor": COLORS["white"],
                "borderwidth": 0,
                "steps": [
                    {
                        "range": [0, 80],
                        "color": "#FEE4E2",
                    },
                    {
                        "range": [80, 100],
                        "color": "#FEF0C7",
                    },
                    {
                        "range": [
                            100,
                            max(
                                130,
                                target_attainment + 10,
                            ),
                        ],
                        "color": "#D1FADF",
                    },
                ],
                "threshold": {
                    "line": {
                        "color": COLORS["red"],
                        "width": 4,
                    },
                    "thickness": 0.8,
                    "value": 100,
                },
            },
        )
    )

    target_gauge_chart = standard_chart_layout(
        target_gauge_chart
    )

    # -----------------------------------------------------
    # CALL ACTIVITY VS SALES
    # -----------------------------------------------------

    activity_scatter_chart = px.scatter(
        representative_data,
        x="Productive_Calls",
        y="Net_Sales_PHP",
        size="Unique_HCPs",
        color="Target_Attainment_Pct",
        hover_name="Rep_Name",
        hover_data={
            "Team": True,
            "Region": True,
            "Productive_Calls": ":,.0f",
            "Unique_HCPs": ":,.0f",
            "Net_Sales_PHP": ":,.0f",
            "Target_Attainment_Pct": ":.1f",
        },
        color_continuous_scale="Turbo",
        size_max=35,
        title=(
            "Productive Calls, HCP Reach and Sales"
        ),
    )

    activity_scatter_chart.update_traces(
        opacity=0.78,
        marker={
            "line": {
                "width": 1,
                "color": COLORS["white"],
            }
        },
    )

    activity_scatter_chart.update_yaxes(
        tickprefix="PHP ",
        tickformat="~s",
        gridcolor="#EAECF0",
    )

    activity_scatter_chart.update_xaxes(
        gridcolor="#EAECF0",
    )

    activity_scatter_chart = standard_chart_layout(
        activity_scatter_chart
    )

    # -----------------------------------------------------
    # TABLE
    # -----------------------------------------------------

    table_data = representative_data.copy()

    table_data = table_data.rename(
        columns={
            "Rep_ID": "Rep ID",
            "Rep_Name": "Representative",
            "Net_Sales_PHP": "Net Sales PHP",
            "Gross_Units": "Gross Units",
            "Unit_Target": "Unit Target",
            "Target_Attainment_Pct": (
                "Target Attainment %"
            ),
            "Productive_Call_Rate_Pct": (
                "Productive Call Rate %"
            ),
            "Unique_HCPs": "HCP Reach",
            "Data_Completeness_Pct": (
                "Data Completeness %"
            ),
        }
    )

    table_columns = [
        "Rep ID",
        "Representative",
        "Team",
        "Region",
        "Net Sales PHP",
        "Gross Units",
        "Unit Target",
        "Target Attainment %",
        "Productive Call Rate %",
        "HCP Reach",
        "Data Completeness %",
    ]

    table_data = table_data[
        table_columns
    ].sort_values(
        "Net Sales PHP",
        ascending=False,
    )

    numeric_rounding = [
        "Net Sales PHP",
        "Target Attainment %",
        "Productive Call Rate %",
        "Data Completeness %",
    ]

    for column in numeric_rounding:
        table_data[column] = (
            table_data[column].round(1)
        )

    table_records = table_data.to_dict(
        "records"
    )

    dash_table_columns = [
        {
            "name": column,
            "id": column,
            "type": (
                "numeric"
                if column in numeric_rounding
                or column in [
                    "Gross Units",
                    "Unit Target",
                    "HCP Reach",
                ]
                else "text"
            ),
        }
        for column in table_columns
    ]

    return (
        format_php(total_sales),
        f"{target_attainment:.1f}%",
        f"{productive_call_rate:.1f}%",
        f"{total_hcp_reach:,.0f}",
        f"{average_completeness:.1f}%",
        f"{return_rate:.2f}%",
        weekly_sales_chart,
        animated_map_chart,
        indication_sales_chart,
        representative_ranking_chart,
        target_gauge_chart,
        activity_scatter_chart,
        table_records,
        dash_table_columns,
    )


# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=8050,
    )