
# Import required libraries
import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

# Read the SpaceX launch data
spacex_df = pd.read_csv("spacex_launch_dash.csv")

# Check that the required columns exist
required_columns = [
    "Launch Site",
    "Payload Mass (kg)",
    "class",
    "Booster Version Category"
]

missing_columns = [
    col for col in required_columns
    if col not in spacex_df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing CSV columns: {missing_columns}. "
        f"Available columns: {spacex_df.columns.tolist()}"
    )

# Convert payload and launch outcome to numeric values
spacex_df["Payload Mass (kg)"] = pd.to_numeric(
    spacex_df["Payload Mass (kg)"], errors="coerce"
)
spacex_df["class"] = pd.to_numeric(
    spacex_df["class"], errors="coerce"
)

# Calculate payload range
min_payload = spacex_df["Payload Mass (kg)"].min()
max_payload = spacex_df["Payload Mass (kg)"].max()

# Handle missing payload values
if pd.isna(min_payload) or pd.isna(max_payload):
    min_payload, max_payload = 0, 10000

# Get launch sites
launch_sites = sorted(
    spacex_df["Launch Site"].dropna().unique().tolist()
)

# Create the Dash application
app = dash.Dash(__name__)

# --------------------------------------------------
# TASK 1 and TASK 3: Dashboard layout
# --------------------------------------------------
app.layout = html.Div(
    style={"padding": "20px"},
    children=[
        html.H1(
            "SpaceX Launch Records Dashboard",
            style={
                "textAlign": "center",
                "color": "#503D36",
                "fontSize": 40
            }
        ),

        html.Label("Select Launch Site:"),

        dcc.Dropdown(
            id="site-dropdown",
            options=[
                {"label": "All Sites", "value": "ALL"}
            ] + [
                {"label": site, "value": site}
                for site in launch_sites
            ],
            value="ALL",
            placeholder="Select a Launch Site here",
            searchable=True,
            clearable=False
        ),

        html.Br(),

        # TASK 2: Successful launch pie chart
        dcc.Graph(
            id="success-pie-chart",
            figure={}
        ),

        html.Br(),

        html.Label("Payload range (Kg):"),

        # TASK 3: Payload range slider
        dcc.RangeSlider(
            id="payload-slider",
            min=0,
            max=10000,
            step=1000,
            marks={
                0: "0",
                2500: "2500",
                5000: "5000",
                7500: "7500",
                10000: "10000"
            },
            value=[
                max(0, min_payload),
                min(10000, max_payload)
            ],
            allowCross=False
        ),

        html.Br(),

        # TASK 4: Payload vs launch outcome scatter chart
        dcc.Graph(
            id="success-payload-scatter-chart",
            figure={}
        )
    ]
)


# --------------------------------------------------
# TASK 2: Pie chart callback
# --------------------------------------------------
@app.callback(
    Output("success-pie-chart", "figure"),
    Input("site-dropdown", "value")
)
def get_pie_chart(entered_site):

    if entered_site == "ALL":
        # Count successful launches at each launch site
        successful_df = spacex_df[
            spacex_df["class"] == 1
        ]

        site_counts = (
            successful_df.groupby("Launch Site")
            .size()
            .reset_index(name="Successful Launches")
        )

        if site_counts.empty:
            fig = px.pie(title="No successful launch data available")
        else:
            fig = px.pie(
                site_counts,
                names="Launch Site",
                values="Successful Launches",
                title="Total Successful Launches by Site"
            )

    else:
        # Count successful and failed launches at the selected site
        filtered_df = spacex_df[
            spacex_df["Launch Site"] == entered_site
        ]

        outcome_counts = (
            filtered_df["class"]
            .map({1: "Success", 0: "Failure"})
            .value_counts()
            .reindex(["Success", "Failure"], fill_value=0)
            .rename_axis("Outcome")
            .reset_index(name="Launch Count")
        )

        fig = px.pie(
            outcome_counts,
            names="Outcome",
            values="Launch Count",
            title=f"Launch Outcomes for {entered_site}"
        )

    fig.update_layout(
        legend_title_text="Launch Site / Outcome"
    )

    return fig


# --------------------------------------------------
# TASK 4: Scatter chart callback
# --------------------------------------------------
@app.callback(
    Output("success-payload-scatter-chart", "figure"),
    [
        Input("site-dropdown", "value"),
        Input("payload-slider", "value")
    ]
)
def get_scatter_chart(entered_site, payload_range):

    low, high = payload_range

    # Filter records by payload range
    filtered_df = spacex_df[
        spacex_df["Payload Mass (kg)"].between(
            low, high, inclusive="both"
        )
    ].copy()

    # Filter by selected launch site
    if entered_site != "ALL":
        filtered_df = filtered_df[
            filtered_df["Launch Site"] == entered_site
        ]

    # Remove rows missing chart data
    filtered_df = filtered_df.dropna(
        subset=[
            "Payload Mass (kg)",
            "class",
            "Booster Version Category"
        ]
    )

    if filtered_df.empty:
        fig = px.scatter(
            title="No launches found for the selected filters"
        )
        fig.add_annotation(
            text="Try selecting a wider payload range or another site.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False
        )
        return fig

    # Plot payload mass against launch outcome
    fig = px.scatter(
        filtered_df,
        x="Payload Mass (kg)",
        y="class",
        color="Booster Version Category",
        title="Payload Mass vs. Launch Outcome",
        labels={
            "Payload Mass (kg)": "Payload Mass (kg)",
            "class": "Launch Outcome (0 = Failure, 1 = Success)",
            "Booster Version Category": "Booster Version"
        },
        hover_data=["Launch Site"]
    )

    fig.update_yaxes(
        tickmode="array",
        tickvals=[0, 1],
        ticktext=["Failure", "Success"]
    )

    return fig


# --------------------------------------------------
# Run the application
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)