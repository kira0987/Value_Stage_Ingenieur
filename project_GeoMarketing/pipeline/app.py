import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime

# Initialize the Dash app with Bootstrap for modern styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Sidebar layout with navigation buttons in divs (no chart)
sidebar = html.Div(
    [
        html.H3("GeoMarketing Dashboard", style={"color": "#007BFF", "font-family": "Inter, sans-serif", "margin-bottom": "1rem"}),
        html.Hr(),
        # Navigation buttons styled as divs
        html.Div(
            [
                html.Div(
                    "Overview",
                    className="nav-button",
                    style={
                        "background-color": "#FFFFFF",
                        "color": "#333",
                        "padding": "10px 15px",
                        "margin-bottom": "0.5rem",
                        "border-radius": "8px",
                        "text-align": "center",
                        "font-family": "Inter, sans-serif",
                        "font-weight": "500",
                        "cursor": "pointer",
                        "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                        "transition": "background-color 0.3s, transform 0.2s",
                    },
                    id="nav-overview",
                ),
                html.Div(
                    "Analytics",
                    className="nav-button",
                    style={
                        "background-color": "#FFFFFF",
                        "color": "#333",
                        "padding": "10px 15px",
                        "margin-bottom": "0.5rem",
                        "border-radius": "8px",
                        "text-align": "center",
                        "font-family": "Inter, sans-serif",
                        "font-weight": "500",
                        "cursor": "pointer",
                        "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                        "transition": "background-color 0.3s, transform 0.2s",
                    },
                    id="nav-analytics",
                ),
                html.Div(
                    "Reports",
                    className="nav-button",
                    style={
                        "background-color": "#FFFFFF",
                        "color": "#333",
                        "padding": "10px 15px",
                        "margin-bottom": "0.5rem",
                        "border-radius": "8px",
                        "text-align": "center",
                        "font-family": "Inter, sans-serif",
                        "font-weight": "500",
                        "cursor": "pointer",
                        "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                        "transition": "background-color 0.3s, transform 0.2s",
                    },
                    id="nav-reports",
                ),
                html.Div(
                    "Settings",
                    className="nav-button",
                    style={
                        "background-color": "#FFFFFF",
                        "color": "#333",
                        "padding": "10px 15px",
                        "margin-bottom": "0.5rem",
                        "border-radius": "8px",
                        "text-align": "center",
                        "font-family": "Inter, sans-serif",
                        "font-weight": "500",
                        "cursor": "pointer",
                        "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                        "transition": "background-color 0.3s, transform 0.2s",
                    },
                    id="nav-settings",
                ),
            ],
            style={"margin-bottom": "1rem"},
        ),
        html.Hr(),
    ],
    id="sidebar",
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "20rem",
        "padding": "1rem",
        "background-color": "#F8F9FA",
        "overflow-y": "auto",
        "border-right": "1px solid #E9ECEF",
        "transition": "width 0.3s",
    },
)

# Chat interface layout
chat_container = html.Div(
    [
        html.Div(
            id="chat-display",
            style={
                "height": "calc(100vh - 150px)",
                "overflow-y": "auto",
                "padding": "1rem",
                "display": "flex",
                "flex-direction": "column",
                "background-color": "#FFFFFF",
                "border-radius": "8px",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
            },
        ),
        dbc.InputGroup(
            [
                dbc.Input(
                    id="chat-input",
                    placeholder="Type your message (e.g., 'Show GeoMarketing insights')...",
                    type="text",
                    style={"border-radius": "8px", "font-family": "Inter, sans-serif"},
                ),
                dbc.InputGroupText(
                    dbc.Button("Send", id="chat-submit", color="primary"),
                ),
            ],
            className="mt-3",
        ),
    ],
    id="chat-container",
    style={"margin-left": "21rem", "padding": 20},
)

# Toggle button for sidebar
toggle_button = html.Div(
    [
        html.I(className="fas fa-bars", style={"font-size": "1.5rem", "color": "#007BFF"}),
    ],
    id="toggle-sidebar",
    style={
        "position": "fixed",
        "top": "1rem",
        "left": "1rem",
        "cursor": "pointer",
        "z-index": "1000",
    },
)

# Main app layout
app.layout = dbc.Container(
    [
        dcc.Store(id="chat-history", data=[]),
        dcc.Store(id="sidebar-state", data=True),  # True = expanded, False = collapsed
        toggle_button,
        sidebar,
        chat_container,
    ],
    fluid=True,
    style={"padding": 0, "background-color": "#E9ECEF", "height": "100vh"},
)

# Function to style chat messages
def create_message(text, sender="user"):
    alignment = "flex-end" if sender == "user" else "flex-start"
    bg_color = "#007BFF" if sender == "user" else "#E9ECEF"
    text_color = "#FFFFFF" if sender == "user" else "#333"
    return html.Div(
        [
            html.P(
                text,
                style={
                    "background-color": bg_color,
                    "color": text_color,
                    "padding": "10px 15px",
                    "border-radius": "15px",
                    "max-width": "60%",
                    "margin": "5px",
                    "font-family": "Inter, sans-serif",
                },
            )
        ],
        style={"display": "flex", "justify-content": alignment},
    )

# Callback to handle chat functionality
@app.callback(
    [Output("chat-display", "children"), Output("chat-history", "data"), Output("chat-input", "value")],
    [Input("chat-submit", "n_clicks"), Input("chat-input", "n_submit")],
    [State("chat-input", "value"), State("chat-history", "data")],
)
def update_chat(n_clicks, n_submit, user_input, chat_history):
    if n_clicks is None and n_submit is None:
        return [], chat_history, ""
    
    if user_input and user_input.strip():
        # Add user message to history
        chat_history.append({"text": user_input, "sender": "user", "time": str(datetime.now())})
        # Simulate bot response (GeoMarketing context)
        bot_response = f"Bot: You said '{user_input}'! How can I assist you with GeoMarketing insights?"
        chat_history.append({"text": bot_response, "sender": "bot", "time": str(datetime.now())})
        
        # Create display elements
        chat_display = [create_message(msg["text"], msg["sender"]) for msg in chat_history]
        
        return chat_display, chat_history, ""
    
    return [], chat_history, ""

# Callback to handle sidebar toggle
@app.callback(
    [
        Output("sidebar", "style"),
        Output("chat-container", "style"),
        Output("toggle-sidebar", "children"),
        Output("sidebar-state", "data"),
    ],
    [Input("toggle-sidebar", "n_clicks")],
    [
        State("sidebar-state", "data"),
        State("sidebar", "style"),
        State("chat-container", "style"),
    ],
)
def toggle_sidebar(n_clicks, sidebar_state, sidebar_style, chat_style):
    if n_clicks is None:
        return sidebar_style, chat_style, html.I(className="fas fa-bars", style={"font-size": "1.5rem", "color": "#007BFF"}), sidebar_state
    
    sidebar_state = not sidebar_state
    sidebar_style = sidebar_style.copy() if sidebar_style else {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "20rem",
        "padding": "1rem",
        "background-color": "#F8F9FA",
        "overflow-y": "auto",
        "border-right": "1px solid #E9ECEF",
        "transition": "width 0.3s",
    }

# Add custom CSS for hover effects on nav buttons
app.css.append_css({
    "external_url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
})
app.css.append_css({
    "external_url": """
    .nav-button:hover {
        background-color: #E9ECEF !important;
        transform: translateY(-2px);
    }
    """
})

if __name__ == "__main__":
    app.run(debug=True)
