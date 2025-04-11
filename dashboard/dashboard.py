from flask import session, request
import dash
from dash import dcc, html, Output, Input
import pandas as pd
import plotly.express as px
import os
import re
from utils.pdf_utils import generate_pdf_from_dashboard, save_pdf_to_mongodb
import datetime


external_stylesheets = ['/static/css/dashboard.css']

def init_dashboard(server):
    app_dash = dash.Dash(
        __name__,
        server=server,
        routes_pathname_prefix='/dashboard/',
        suppress_callback_exceptions=True,
        external_stylesheets=external_stylesheets
    )

    app_dash.layout = html.Div([  
        html.Div([ 
            html.Nav([
                html.Div([
                    html.A("🏠Home", href="/", className="nav-link"),
                ], className="nav-left"),

                html.Div([
                    html.A("👤", href="/profile", className="nav-link"),
                ], className="nav-right"),
            ], className="navbar"),
            html.H1("🔍 Amazon Review Sentiment Dashboard", className="title"),
            html.Div(id="product-url", className="product-url"),
            html.Div([
                html.Button("💾 Save Dashboard as PDF", id="save-pdf-button", n_clicks=0, className="save-pdf-btn"),
                html.Div(id="pdf-save-status", className="pdf-status")
            ], className="save-button-container-inline"),  # Added inline container for the button and status

            html.Div(id='stats-container', className='grid stats'),

            html.Div([  
                html.Div(id='chart-1', className='chart-card'),
                html.Div(id='chart-2', className='chart-card')
            ], className='grid charts-row'),

            html.Div([  
                html.Div(id='chart-3', className='chart-card'),
                html.Div(id='chart-4', className='chart-card')
            ], className='grid charts-row'),

            html.Div(id='comments-row', className='grid comments-row')
        ], className="container"),

        dcc.Interval(id='interval', interval=3000, n_intervals=0)
    ])

    # ⬅️ MAIN DASHBOARD UPDATE CALLBACK
    @app_dash.callback(
        Output('product-url', 'children'),
        Output('stats-container', 'children'),
        Output('chart-1', 'children'),
        Output('chart-2', 'children'),
        Output('chart-3', 'children'),
        Output('chart-4', 'children'),
        Output('comments-row', 'children'),
        Input('interval', 'n_intervals')
    )
    def update_dashboard(_):
        product_url = session.get('last_url', '')
        if product_url:
            product_url_text = html.Div([
                html.Strong("Product URL: "),
                html.A("View Product on Amazon", href=product_url, target="_blank")
            ])
        else:
            product_url_text = "Product URL: Not available"

        # Load Data
        if not os.path.exists("sentiment_results.csv"):
            df = pd.DataFrame(columns=[
                "text", "rating", "date", "verified purchase", "length",
                "sentiment", "positive_score", "neutral_score", "negative_score"
            ])
        else:
            df = pd.read_csv("sentiment_results.csv")
            df.columns = df.columns.str.strip()
            df['sentiment'] = df['sentiment'].str.lower().str.strip()
            if 'verified purchase' not in df.columns:
                df['verified purchase'] = False
            else:
                df['verified purchase'] = df['verified purchase'].astype(str).str.lower().isin(['true', 'yes', '1'])
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        sentiment_counts = df['sentiment'].value_counts().to_dict()
        total_reviews = len(df)
        verified_percentage = 100  # always 100%

        pastel_colors = ['#FFB6C1', '#ADD8E6', '#FFDAB9', '#98FB98', '#E6E6FA']

        # Graphs
        length_fig = px.histogram(df, x='length', nbins=20, title='Review Length Distribution',
                                  color_discrete_sequence=[pastel_colors[0]])

        rating_counts = df['rating'].value_counts().sort_index().reset_index()
        rating_counts.columns = ['rating', 'count']
        rating_fig = px.bar(rating_counts, x='rating', y='count', title='Rating Distribution',
                            color_discrete_sequence=[pastel_colors[1]])

        time_fig = px.line(df.sort_values(by="date"), x='date', y='positive_score', title='Positive Score Trend',
                           color_discrete_sequence=[pastel_colors[2]])

        sentiment_avg = df[['positive_score', 'neutral_score', 'negative_score']].mean().reset_index()
        sentiment_avg.columns = ['Sentiment', 'Average Score']
        score_fig = px.bar(sentiment_avg, x='Sentiment', y='Average Score',
                           title='Average Sentiment Scores',
                           color='Sentiment', color_discrete_sequence=pastel_colors)

        for fig in [length_fig, rating_fig, time_fig, score_fig]:
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Poppins", size=13),
                margin=dict(t=40, l=20, r=20, b=30),
            )

        # Stats
        stats = [
            html.Div([html.H4("😊 Positive"), html.H2(sentiment_counts.get('positive', 0))], className="stat-card positive"),
            html.Div([html.H4("😐 Neutral"), html.H2(sentiment_counts.get('neutral', 0))], className="stat-card neutral"),
            html.Div([html.H4("😞 Negative"), html.H2(sentiment_counts.get('negative', 0))], className="stat-card negative"),
            html.Div([html.H4("✅ Verified Users"), html.H2(f"{verified_percentage}%")], className="stat-card verified"),
        ]

        # Comments
        top_positive = df.sort_values(by='positive_score', ascending=False).iloc[0]['text'] if not df.empty else 'N/A'
        top_negative = df.sort_values(by='negative_score', ascending=False).iloc[0]['text'] if not df.empty else 'N/A'

        positive_comment = html.Div([
            html.H4("🌟 Top Positive Review", className="comment-title"),
            html.P(f"“{top_positive}”", className="comment-text")
        ], className="comment-card positive-comment")

        negative_comment = html.Div([
            html.H4("💔 Top Negative Review", className="comment-title"),
            html.P(f"“{top_negative}”", className="comment-text")
        ], className="comment-card negative-comment")

        return (
            product_url_text,
            stats,
            dcc.Graph(figure=length_fig),
            dcc.Graph(figure=rating_fig),
            dcc.Graph(figure=time_fig),
            dcc.Graph(figure=score_fig),
            [positive_comment, negative_comment]
        )

    # ⬅️ SEPARATE CALLBACK FOR PDF SAVING
    @app_dash.callback(
        Output('pdf-save-status', 'children'),
        Input('save-pdf-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def save_dashboard(n_clicks):
        if n_clicks and n_clicks > 0:
            try:
                email = session.get('user', {}).get('email')
                session_cookie = request.cookies.get('session')

                if not email or not session_cookie:
                    return "❌ User not logged in."

                # Read product title from product_title.txt
                try:
                    with open('product_title.txt', 'r', encoding='utf-8') as f:
                        product_title = f.read().strip()
                except FileNotFoundError:
                    product_title = "dashboard"

                # Sanitize and truncate title for filename
                safe_title = re.sub(r'\W+', '_', product_title)[:50]  # Keep it safe and short
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{safe_title}_{timestamp}.pdf"

                dashboard_url = "http://localhost:5000/dashboard/"
                pdf_bytes = generate_pdf_from_dashboard(dashboard_url, session_cookie)

                save_pdf_to_mongodb(server.db, pdf_bytes, email, filename)

                return "✅ Dashboard saved to your profile!"
            except Exception as e:
                return f"❌ Error saving PDF: {str(e)}"
        return ""
    return app_dash.server

