import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import plotly.figure_factory as ff

import pandas as pd
import numpy as np
import datetime
import base64
import urllib.request
import os
import stylecloud


#####   source dashboard: https://github.com/plotly/dash-sample-apps/blob/master/apps/dash-manufacture-spc-dashboard/app.py

# __name__ enables app to look for CSS in assets folder
# extenal_stylesheets enable bootstrap styling
# meta tags for media queries
app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])  
app.config.suppress_callback_exceptions = True  ## NEEDED for dynamic multitab 
server = app.server 

###### Intialize banner
def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id="banner-text",
                children=[
                    html.H5("Indonesia Trending Youtube Video Analysis Dashboard"),
                    html.H6("From Jul 8th 2020 - Jul 14th 2020"),
                    html.H6("Data Source: Youtube APIv3, www.socialblade.com", style={'font-size': '1.25rem'}),
                ],
            ),
            html.Div(
                id="banner-logo",
                children=[
                    html.Img(id="yt_logo", src='assets/youtube_logo.jpg'),
                    html.Img(id="logo", src='assets/plotly_logo.png'),
                    html.Button(id="learn-more-button", children="LEARN MORE", n_clicks=0),
                ],
            ),
        ],
    )

###### create tabs
def build_tabs():
    return html.Div(
        id="tabs",
        className="tabs",
        children=[
            dcc.Tabs(
                id="app-tabs",
                value="tab1",   # starting tab
                className="custom-tabs",
                children=[
                    dcc.Tab(
                        id="Daily-tab",
                        label="Daily Dashboard",
                        value="tab1",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                    dcc.Tab(
                        id="Weekly-tab",
                        label="Weekly Dashboard",
                        value="tab2",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                ],
            )
        ],
    )

###### create modal
def generate_modal():
    return html.Div(
        id="markdown",
        className="modal",
        children=(
            html.Div(
                id="markdown-container",
                className="markdown-container",
                children=[
                    html.Div(
                        className="close-container",
                        children=html.Button(
                            "Close",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton",
                        ),
                    ),
                    html.Div(
                        className="markdown-text",
                        children=dcc.Markdown(
                            children=(
                            """
                            ###### What is this dashboard about?
                            This is a dashboard for created for an analysis on Indonesia Trending Youtube Videos from 8th July 2020 to 14th July 2020 
                            ###### What does this app shows?
                            Daily and Weekly summary statistics for Indonesia's Top 200 daily trending videos.
                            
                            The Daily Tab shows top ranked videos, top channels, published date, publish hour, and much more for the selected dates. 
                            Change the dates on the `dropdown` to change dates to filter on the daily tabs.
                            
                            The Weekly Tab shows a summary of statistics for the week  with charts from the daily tabs, wordclouds, corrleations and more.
                            Slide on the `date range bar` to change the dates to filter on the weekly tabs.
                            """
                            )
                        ),
                    ),
                ],
            )
        ),
    )


####### Reading in Data
# reads dataframe
df = pd.read_pickle('data/final.pkl')

# list of all possible dates
date_list = np.unique(df['trending_date'])
date_list.sort()
date_list_formatted = [elem.strftime('%Y-%m-%d') for elem in date_list]
slider_marks = {}

# labels to range slider
for ind, elem in enumerate(date_list):
    temp = {}
    temp['label'] = elem.strftime('%b-%d')
    temp['style'] = {'color': '#ffffff'}
    slider_marks[ind] = temp

# no duplicates and keeps only the first occurance of trending (for publish date, etc)
no_dups_f = df.sort_values('trending_date', ascending = True)
no_dups_f = no_dups_f.drop_duplicates(subset='video_id', keep='first')

# no duplicates and keeps last occurance for views, comments, etc
no_dups_l = df.sort_values('trending_date', ascending = True)
no_dups_l = no_dups_l.drop_duplicates(subset='video_id', keep='last')  
   
########## Main App Layout
app.layout = html.Div(
    id="big-app-container",
    children=[
        build_banner(),
        html.Div(
            id="app-container",
            children=[
                build_tabs(),
                # Main app
                html.Div(id="app-content"),
            ]
        ),
        generate_modal()
    ]
)


#### Callbacks for tabs
@app.callback(
    [Output("app-content", "children")],
    [Input("app-tabs", "value")]
)
def render_tab_content(tab_switch):
    if tab_switch == "tab1":
        return  [html.Div(
                    id="tab1-container",
                    children=[
                        # Tab 1 dropdowns
                        html.Div(children = [
                            html.Br(),
                            html.Label(id="date_selector_label", className='col-sm-12 col-lg-2', children="Select Date: ", style={'marginLeft': '5rem', 'marginTop': '3rem'}),
                            html.Br(),
                            html.Div(className = 'col-sm-12 col-md-6 col-lg-3', children =[ 
                                dcc.Dropdown(
                                id='date_selector',
                                options=[{'label': elem, 'value': date_list[ind]} for ind, elem in enumerate(date_list_formatted)],
                                value = date_list[0])],
                                style={'marginTop': '3rem'}),
                        ], className = 'row'),
                        
                        html.Br(),
                        
                        # Tab 1 first row
                        html.Div(children=[
                            # barcharts for number of categories
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Category Count of Trending Videos'),
                                    dcc.Graph(id='categories_graph_daily'), 
                            ]),
                            
                            # Top Trending Videos Today (Table)
                            html.Div(className = "col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Top 10 Ranked Trending Video Today'),
                                    html.Br(),
                                    html.Div(id='top_rank_daily')
                                ]
                            ),
                        ], className = 'row'),
                        

                        # Tab 1 second row  
                        html.Div(children=[
                            # barchart most viewed video today
                            html.Div(className="col-sm-12 col-lg-4",
                                children = [
                                    html.Div(className="section-banner", children='Trending Videos by Views Today'),
                                    dcc.Graph(id='most_viewed_daily'), 
                            ]),
                            # barchart most liked video today
                            html.Div(className="col-sm-12 col-lg-4",
                                children = [
                                    html.Div(className="section-banner", children='Trending Videos by Likes Today'),
                                    dcc.Graph(id='most_liked_daily'), 
                            ]),
                            # barchart most comment video today
                            html.Div(className="col-sm-12 col-lg-4",
                                children = [
                                    html.Div(className="section-banner", children='Trending Videos by Comments Today'),
                                    dcc.Graph(id='most_comment_daily'), 
                            ]),
                        ], className = 'row'),
                        
                        
                        # Tab 1 third row  
                        html.Div(children=[
                            # when is trending video today published
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Trending Videos by Published Date'),
                                    dcc.Graph(id='trending_video_publish_daily')
                            ]),
                            # stacked barchart publishing hour by category for todays video
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Trending Videos by Published Hour for Top 5 Categories'),
                                    dcc.Graph(id='published_hour_daily'), 
                            ]),
                        ], className = 'row'),
                        
                        # Tab 1 fourth row  
                        html.Div(children=[
                            # top 10 channels by trending video count today
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Top 10 Channels by Video Trending Count'),
                                    html.Div(id='top_channel_daily'), 
                            ]),
                            # geographic distribution of channel
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Country of Origin for Channels'),
                                    dcc.Graph(id='country_origin_channel_daily'), 
                            ]),
                        ], className = 'row'),
                                                
                    ],
                )]
    else:
        return [html.Div(
                    id="tab2-container",
                    children=[
                        # Tab 2 date slider
                        html.Div([
                            html.Label(id="date_range_label", className='col-sm-12', children="Select Date Range: ", style={'marginLeft': '5rem', 'marginTop': '3rem'}),
                            html.Br(),
                            dcc.RangeSlider(
                                id = 'date_slider',
                                updatemode = 'mouseup', #don't let it update till mouse released
                                min = 0,
                                max = len(date_list) - 1,
                                value = [0, len(date_list) - 1],
                                marks=slider_marks,
                            )]),
                        
                        html.Br(),
                        
                        # Tab 2 first row
                        html.Div(children=[
                            # barcharts for number of categories (unique)
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Category Count of Trending Videos (Unique)'),
                                    dcc.Graph(id='categories_graph_weekly'), 
                            ]),
                            
                            # Correlation plot of all variables
                            html.Div(className = "col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Correlation of Variables (Unique)'),
                                    dcc.Graph(id='correlation_variables_weekly'),
                                ]
                            ),
                        ], className = 'row'),  
                        
                        # Tab 2 second row  
                        html.Div(children=[
                            # barchart most viewed video weekly
                            html.Div(className="col-sm-12 col-lg-4",
                                children = [
                                    html.Div(className="section-banner", children='Trending Videos by Views Thus Far'),
                                    dcc.Graph(id='most_viewed_weekly'), 
                            ]),
                            # barchart most liked video weekly
                            html.Div(className="col-sm-12 col-lg-4",
                                children = [
                                    html.Div(className="section-banner", children='Trending Videos by Likes Thus Far'),
                                    dcc.Graph(id='most_liked_weekly'), 
                            ]),
                            # barchart most comment video weekly
                            html.Div(className="col-sm-12 col-lg-4",
                                children = [
                                    html.Div(className="section-banner", children='Trending Videos by Comments Thus Far'),
                                    dcc.Graph(id='most_comment_weekly'), 
                            ]),
                        ], className = 'row'),
                        
                        # Tab 2 third row  
                        html.Div(children=[
                            # wordcloud row
                            html.Div(className = 'col-lg-12',
                                children = [
                                    html.Div(className="section-banner", children='Word Cloud [Title, Desc, Tags] ..... (Might take several minutes to load)'),
                                    html.Div(id='word_cloud_title')
                            ])
                        ], className = 'row'),
                        
                        html.Br(),

                        # Tab 2 fourth row  
                        html.Div(children=[
                            # when is trending video published
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Trending Unique Videos by Published Date'),
                                    dcc.Graph(id='trending_video_publish_weekly')
                            ]),
                            # publish hour of trending videos
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Trending Videos by Published Hour for Top 5 Categories (Unique)'),
                                    dcc.Graph(id='published_hour_weekly'), 
                            ]),
                        ], className = 'row'),
                        
                        # Tab 2 fourth row  
                        html.Div(children=[
                            # top 10 channels by trending video count
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Top 10 Channels by Video Trending Count in Period'),
                                    html.Div(id='top_channel_weekly'), 
                            ]),
                            # geographic distribution of channel
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Country of Origin for Channels (Unique)'),
                                    dcc.Graph(id='country_origin_channel_weekly'), 
                            ]),
                        ], className = 'row'),
                        
                        # Tab 2 fifth row  
                        html.Div(children=[
                            # Social Blade rankings of channels
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Social Blade Rankings of Channels (Unique)'),
                                    dcc.Graph(id='sb_rank_weekly'),
                            ]),
                            # Channel video views in past two weeks
                            html.Div(className="col-sm-12 col-lg-6",
                                children = [
                                    html.Div(className="section-banner", children='Channel Views within the past 2 weeks'),
                                    dcc.Graph(id='channel_views_past_weekly')
                            ]),
                        ], className = 'row'),
                    ])            
                ]


# ======= Callbacks for modal popup =======
@app.callback(
    Output("markdown", "style"),
    [Input("learn-more-button", "n_clicks"), Input("markdown_close", "n_clicks")],
)
def update_click_output(button_click, close_click):
    ctx = dash.callback_context

    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "learn-more-button":
            return {"display": "block"}

    return {"display": "none"}



# ========= Weekly callbacks =================
###################### Tab 2 Row 1 Charts
@app.callback(
    Output('categories_graph_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_category_bar_weekly(value = [0, len(date_list) - 1]): 
    # filter date
    filtered_df = no_dups_f[(no_dups_f['trending_date'] >= date_list[value[0]]) & (no_dups_f['trending_date'] <= date_list[value[1]])]
    
    temp = filtered_df['categoryIdName'].value_counts().reset_index()
    fig = px.bar(temp, x="index", y="categoryIdName", text='categoryIdName', labels={'index': 'Categories', 'categoryIdName': 'Count of Videos'})
    fig.update_traces(texttemplate='%{text:.0d}', textposition='inside')  #can add textposition here (inside/outside)
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                      margin=dict(l=10, r=10, t=10, b=10), yaxis_showgrid=False) #can add transition duration here
    fig.update_yaxes(showticklabels=False)
    return fig


@app.callback(
    Output('correlation_variables_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_corr_weekly(value = [0, len(date_list) - 1]):
    # filter date
    filtered_df = no_dups_f[(no_dups_f['trending_date'] >= date_list[value[0]]) & (no_dups_f['trending_date'] <= date_list[value[1]])]
    
    # make correlation df and round to 2 decimals
    filtered_df = filtered_df[['view_count', 'likes', 'dislikes', 'comment_count', 'rank', 'curr_subs_num']].corr()
    curr_cols = list(filtered_df.columns)
    filtered_df = filtered_df[curr_cols[::-1]]
    filtered_df = np.around(filtered_df, 2)

    x = list(filtered_df.columns)
    y = list(filtered_df.index)
    z_text = np.array(filtered_df.values)
    z = np.array(filtered_df.values)

    # create correlation plots
    fig = ff.create_annotated_heatmap(z, x=x, y=y, annotation_text=z_text, colorscale='viridis')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                      margin=dict(l=10, r=10, t=10, b=10), yaxis_showgrid=False) #can add transition duration here
    return fig
    
############### Tab 2 Row 2 Charts
@app.callback(
    Output('most_viewed_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_viewed_weekly(value = [0, len(date_list) - 1]): 
    filtered_df = df[(df['trending_date'] >= date_list[value[0]]) & (df['trending_date'] <= date_list[value[1]])]
    
    # no duplicates and keeps last occurance for views, comments, etc
    filtered_df = filtered_df.sort_values('trending_date', ascending = True)
    filtered_df = filtered_df.drop_duplicates(subset='video_id', keep='last')
    
    filtered_df = filtered_df.sort_values('view_count', ascending = True)
    filtered_df = filtered_df[-10:]
    
    def shorten_title(x, num_chars):
        if len(x) < num_chars:
            return x
        
        if x == 'BLACKPINK - \'How You Like That\' M/V':
            return x[:num_chars-1] + '...1'
        else:
            return x[:num_chars] + '...' 
    
    # map to sorten title 
    filtered_df['title_short'] = filtered_df['title'].apply(lambda x: shorten_title(x, 20))

    fig = px.bar(filtered_df, x="view_count", y="title_short", text='view_count', 
                 hover_data={'view_count': ':.3s',
                             'title': True,
                             'title_short': False})
    fig.update_traces(texttemplate='%{text:.2s}', textposition='inside')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                   margin=dict(l=50, r=10, t=10, b=10), xaxis_showgrid=False) #can add transition duration here   # margin=dict(l=200, r=10, t=10, b=10),
    fig.update_yaxes(title='', automargin = True)
    return fig
    
@app.callback(
    Output('most_liked_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_liked_weekly(value = [0, len(date_list) - 1]): 
    filtered_df = df[(df['trending_date'] >= date_list[value[0]]) & (df['trending_date'] <= date_list[value[1]])]
    
    # no duplicates and keeps last occurance for views, comments, etc
    filtered_df = filtered_df.sort_values('trending_date', ascending = True)
    filtered_df = filtered_df.drop_duplicates(subset='video_id', keep='last')
    
    filtered_df = filtered_df.sort_values('likes', ascending = True)
    filtered_df = filtered_df[-10:]
    
    def shorten_title(x, num_chars):
        if len(x) < num_chars:
            return x
        
        if x == 'BLACKPINK - \'How You Like That\' M/V':
            return x[:num_chars-1] + '...1'
        else:
            return x[:num_chars] + '...' 
    
    # map to sorten title 
    filtered_df['title_short'] = filtered_df['title'].apply(lambda x: shorten_title(x, 20))

    fig = px.bar(filtered_df, x="likes", y="title_short", text='likes', 
                 hover_data={'likes': ':.3s',
                             'title': True,
                             'title_short': False})
    fig.update_traces(texttemplate='%{text:.2s}', textposition='inside')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                   margin=dict(l=50, r=10, t=10, b=10), xaxis_showgrid=False) #can add transition duration here   # margin=dict(l=200, r=10, t=10, b=10),
    fig.update_yaxes(title='', automargin = True)
    return fig

@app.callback(
    Output('most_comment_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_comment_weekly(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] >= date_list[value[0]]) & (df['trending_date'] <= date_list[value[1]])]
    
    # no duplicates and keeps last occurance for views, comments, etc
    filtered_df = filtered_df.sort_values('trending_date', ascending = True)
    filtered_df = filtered_df.drop_duplicates(subset='video_id', keep='last')
    
    filtered_df = filtered_df.sort_values('comment_count', ascending = True)
    filtered_df = filtered_df[-10:]
    
    def shorten_title(x, num_chars):
        if len(x) < num_chars:
            return x
        
        if x == 'BLACKPINK - \'How You Like That\' M/V':
            return x[:num_chars-1] + '...1'
        elif x == 'Tiara Andini - Maafkan Aku #TerlanjurMencinta (Official Music Video)':
            return x[:num_chars-1] + '...1'
        elif x == 'Ziva Magnolya - Tak Sanggup Melupa #TerlanjurMencinta (Official Music Video)':
            return x[:num_chars-1] + '...1'
        elif x == 'Lyodra - Mengapa Kita #TerlanjurMencinta (Official Music Video)':
            return x[:num_chars-1] + '...1'
        else:
            return x[:num_chars] + '...' 
    
    # map to sorten title 
    filtered_df['title_short'] = filtered_df['title'].apply(lambda x: shorten_title(x, 20))

    fig = px.bar(filtered_df, x="comment_count", y="title_short", text='comment_count', 
                 hover_data={'comment_count': ':.3s',
                             'title': True,
                             'title_short': False})
    fig.update_traces(texttemplate='%{text:.2s}', textposition='inside')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                   margin=dict(l=50, r=10, t=10, b=10), xaxis_showgrid=False) #can add transition duration here   # margin=dict(l=200, r=10, t=10, b=10),
    fig.update_yaxes(title='', automargin = True)
    return fig


    
################# Tab 2 Row 3 Charts    
def return_html_image(filepath):
    currfile = open(filepath, 'rb')
    encoded_image = base64.b64encode(currfile.read())
    decoded_image = html.Img(src='data:image/jpg;base64,{}'.format(encoded_image.decode()), id='word_cloud_title_img')
    currfile.close()
    return html.Div(children=decoded_image)

@app.callback(
    Output('word_cloud_title', 'children'),
    [Input('date_slider', 'value')])
    
def update_word_cloud_weekly(value = [0, len(date_list) - 1]): 
    filtered_df = no_dups_f[(no_dups_f['trending_date'] >= date_list[value[0]]) & (no_dups_f['trending_date'] <= date_list[value[1]])]
    
    # process title
    filtered_df['cleaned_text'] = filtered_df['title_cleaned'].apply(lambda x: ' '.join(x))
    long_string = ','.join(list(filtered_df['cleaned_text'].values))
    stylecloud.gen_stylecloud(text=long_string, icon_name='fab fa-youtube', max_words=200, 
                              palette='cartocolors.diverging.TealRose_7', background_color="black", 
                              output_name='data/100.jpg')
    
    # process description
    filtered_df['cleaned_text'] = filtered_df['desc_cleaned'].apply(lambda x: ' '.join(x))
    long_string = ','.join(list(filtered_df['cleaned_text'].values))
    stylecloud.gen_stylecloud(text=long_string, icon_name='fab fa-youtube', max_words=200, 
                              palette='cartocolors.diverging.TealRose_7', background_color="black", 
                              output_name='data/101.jpg')
    
    # process tags
    def tags_split(x):
        if x == '[none]':
            return []
        else:
            return x.split('|')
    
    filtered_df['tags_split'] = filtered_df['tags'].apply(lambda x: tags_split(x))
    filtered_df['cleaned_text'] = filtered_df['tags_split'].apply(lambda x: ' '.join(x))
    long_string = ','.join(list(filtered_df['cleaned_text'].values))
    stylecloud.gen_stylecloud(text=long_string, icon_name='fas fa-hashtag', max_words=200, 
                              palette='cartocolors.diverging.TealRose_7', background_color="black", 
                              output_name='data/102.jpg')
    
    final = return_html_image('data/100.jpg')
    final2 = return_html_image('data/101.jpg')
    final3 = return_html_image('data/102.jpg')
    
    return [final, final2, final3]



########## Tab 2 Row 4 Charts
@app.callback(
    Output('trending_video_publish_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_publish_day_weekly(value = [0, len(date_list) - 1]): 
    filtered_df = no_dups_f[(no_dups_f['trending_date'] >= date_list[value[0]]) & (no_dups_f['trending_date'] <= date_list[value[1]])]
    filtered_df = filtered_df.resample('D', on='publishedAt').count()['video_id'].reset_index()
    filtered_df.columns = ['Published Day', 'Count of Videos']
    filtered_df['color'] = '#636EFB'
    filtered_df.iloc[-1,2] = 'Yellow'
   
    fig = px.bar(filtered_df, x="Published Day", y="Count of Videos", text='Count of Videos', color = 'color', hover_data={'color': False})
    fig.update_traces(texttemplate='%{text:.0d}', textposition='inside')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                   margin=dict(l=10, r=10, t=10, b=10), yaxis_showgrid=False, showlegend=False) #can add transition duration here   # margin=dict(l=200, r=10, t=10, b=10),

    return fig


@app.callback(
    Output('published_hour_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_publish_hour_weekly(value = [0, len(date_list) - 1]): 
    filtered_df = no_dups_f[(no_dups_f['trending_date'] >= date_list[value[0]]) & (no_dups_f['trending_date'] <= date_list[value[1]])]
        
    def create_bins():
        ans = []
        for i in range(24):
            ans.append(str(i) + ':00')
            ans.append(str(i) + ':30')
        return ans
        
    bins = create_bins()
    count_bins = pd.DataFrame()
    count_bins['bins'] = bins

    temp = filtered_df.groupby(['publish_cat', 'categoryIdName']).agg('count')['title'].reset_index()
    # filter only top5 categories for the day
    top_5 = no_dups_f.groupby(['categoryIdName']).agg('count')['title'].reset_index()
    top_5 = top_5.sort_values('title', ascending = False)
    top_5 = top_5['categoryIdName'].values[:5]
    
    def map_others(x):
        if x not in top_5:
            return 'Others'
        else:
            return x

    temp['categoryIdName'] = temp['categoryIdName'].apply(lambda x: map_others(x)) 

    # put into appropriate format
    count_bins = pd.merge(count_bins, temp, left_on = 'bins', right_on = 'publish_cat', how = 'left')
    count_bins.drop(['publish_cat'], axis = 1, inplace = True)
    count_bins['title'] = count_bins['title'].fillna(0)
    count_bins['title'] = count_bins['title'].astype(int)
    count_bins = count_bins.groupby(['bins', 'categoryIdName']).agg('sum').reset_index()

    bins_pivot = count_bins.pivot(index='bins', columns='categoryIdName', values='title')
    bins_pivot = bins_pivot.reindex(bins)
        
    bins_pivot = bins_pivot.reset_index()
    bins_pivot = bins_pivot.fillna(0)
    bins_pivot = bins_pivot.T.reset_index()
    
    # create bar chart
    stacked_data = []
    for i in range(1, bins_pivot.shape[0]):
         stacked_data.append(go.Bar(name = bins_pivot.loc[i, 'categoryIdName'], x = bins, y = bins_pivot.iloc[i,:][1:].values)) 
    
    stacked_data = stacked_data[::-1]
    
    fig = go.Figure(data=stacked_data)
    # Change the bar mode
    fig.update_layout(barmode='stack', xaxis_title = 'Hour of Publish (WIB)', yaxis_title = 'Count of Videos')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
               margin=dict(l=10, r=10, t=10, b=10), yaxis_showgrid=False)  #can add transition duration here
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    return fig

###################### Tab 2 Row 5 Charts
@app.callback(
    Output('top_channel_weekly', 'children'),
    [Input('date_slider', 'value')])
    
def update_channel_table_weekly(value = [0, len(date_list) - 1]): 
    filtered_df = df[(df['trending_date'] >= date_list[value[0]]) & (df['trending_date'] <= date_list[value[1]])]
        
    filtered_df = filtered_df.groupby(['channelTitle', 'avatar_url', 'channel_type','curr_subs']).agg('count')['video_id'].reset_index()
    filtered_df = filtered_df.sort_values('video_id', ascending = False)
    filtered_df = filtered_df[:10]
    
    images_decoded_list = [] 
    # decode image to HTML to show in table
    for idx, elem in enumerate(filtered_df['avatar_url'].values):
        if elem != '':
            urllib.request.urlretrieve(elem, 'data/' + str(idx) + '.jpg')
            image_filename = 'data/' + str(idx) + '.jpg' # replace with your own image
        else:
            image_filename = 'data/test.jpg' # replace with your own image
            
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())
        decoded_image = html.Img(src='data:image/jpg;base64,{}'.format(encoded_image.decode()))
        images_decoded_list.append(decoded_image)
    
    filtered_df['images'] = images_decoded_list    
    filtered_df.drop(['avatar_url'], axis = 1, inplace = True)
    filtered_df = filtered_df[['channelTitle', 'images', 'channel_type', 'curr_subs', 'video_id']]
    filtered_df.columns = ['Channel Title', 'Channel Avatar', 'Channel Category', 'Current Subscribers', 'Trending Videos Count']
    
    return dbc.Table.from_dataframe(filtered_df, bordered=True, responsive="sm", id="top_channel_daily_table")

@app.callback(
    Output('country_origin_channel_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_channel_origin_weekly(value = [0, len(date_list) - 1]): 
    filtered_df = df[(df['trending_date'] >= date_list[value[0]]) & (df['trending_date'] <= date_list[value[1]])]
    
    filtered_df = filtered_df.sort_values('trending_date', ascending = True)
    filtered_df = filtered_df.drop_duplicates(subset='video_id', keep = 'last')
    
    # map into 3 letters iso-alpha code
    code_mapping = {'AU': 'AUS', 'CN': 'CHN', 'DE': 'DEU', 'ES': 'ESP', 'GB': 'GBR','GH': 'GHA','ID': 'IDN', 'IE': 'IRL', 'IN': 'IND', 'IT': 'ITA',
                    'JP': 'JPN', 'KR': 'KOR', 'MY': 'MYS', 'RU': 'RUS', 'US': 'USA', 'VN': 'VNM'}
    
    filtered_df = filtered_df.groupby(['country']).agg('count')['video_id'].reset_index()
    filtered_df = filtered_df[filtered_df['country'] != '']
    filtered_df['iso_alpha'] = filtered_df['country'].apply(lambda x: code_mapping[x])
    filtered_df.columns = ['country', 'count_of_videos', 'iso_alpha']
    
    # create chloropleth map
    fig = px.choropleth(filtered_df, locations ="iso_alpha",
                        color="count_of_videos",
                        scope = 'world',
                        projection = 'natural earth',
                        range_color = (1,30))
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, geo=dict(bgcolor='#161a28'), margin=dict(l=10, r=10, t=10, b=10),
                      coloraxis_showscale=False)
    return fig



####################### Tab 2 Row 6 Charts
@app.callback(
    Output('sb_rank_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_sb_rank_weekly(value = [0, len(date_list) - 1]): 
    filtered_df = df[(df['trending_date'] >= date_list[value[0]]) & (df['trending_date'] <= date_list[value[1]])]
    
    # drop duplicates
    filtered_df = filtered_df.sort_values('trending_date', ascending = True)
    filtered_df = filtered_df.drop_duplicates(subset='video_id', keep='last')
    
    filtered_df = filtered_df.groupby(['rank_y', 'channel_type']).agg('count')['video_id'].reset_index()
    filtered_df.sort_values('video_id', inplace = True, ascending = False)
    def replace_empty(x):
        if x == '':
            return 'N/A'
        else:
            return x
        
    filtered_df['rank_y'] = filtered_df['rank_y'].apply(lambda x: replace_empty(x))
    filtered_df['video_id'] = filtered_df['video_id'].astype(int)
    
    # take top 5 category
    top_5 = filtered_df.groupby(['channel_type']).agg('sum')['video_id'].reset_index()
    top_5 = top_5.sort_values(by='video_id', ascending = False)
    top_5 = top_5['channel_type'].values[:5]

    def map_others(x):
        if x not in top_5:
            return 'Others'
        else:
            return x
    
    # map to others for those category not in top 5
    filtered_df['channel_type'] = filtered_df['channel_type'].apply(lambda x: map_others(x))
    filtered_df = filtered_df.groupby(['rank_y', 'channel_type']).agg('sum').reset_index()
    filtered_df = filtered_df.pivot(index = 'channel_type', columns = 'rank_y', values = 'video_id').reset_index()
    filtered_df = filtered_df.fillna(0)
    all_ranks = ['channel_type', 'A++', 'A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'D-', 'N/A']
    filtered_df = filtered_df[all_ranks]
    
    # create stacked bar chart
    stacked_data = []
    for i in range(0, filtered_df.shape[0]):
         stacked_data.append(go.Bar(name = filtered_df.loc[i, 'channel_type'], x = filtered_df.columns[1:], y = filtered_df.iloc[i,:][1:].values))

    stacked_data = stacked_data[::-1]
    fig = go.Figure(data=stacked_data)
    # Change the bar mode
    fig.update_layout(barmode='stack', xaxis_title = 'Social Blade Rank', yaxis_title = 'Count of Videos')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
               margin=dict(l=10, r=10, t=10, b=10), yaxis_showgrid=False)  #can add transition duration here
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    return fig


@app.callback(
    Output('channel_views_past_weekly', 'figure'),
    [Input('date_slider', 'value')])
    
def update_channel_views_weekly(value = [0, len(date_list) - 1]): 
    filtered_df = df.copy()
    filtered_df = filtered_df[['channelTitle', 'past_view_gains']]
        
    temp = filtered_df['past_view_gains'].apply(pd.Series)
    temp = temp.iloc[:,9:-1]
    final = filtered_df.join(temp, how = 'left')
    final = final.drop_duplicates(subset = 'channelTitle', keep='last')
    final = final.sort_values('channelTitle', ascending = True)
    final = final.T
    final.columns = final.iloc[0,:]
    final = final.iloc[2:,:]
    final.index = pd.to_datetime(final.index, format='%Y-%m-%d')
    
    # create the line chart
    fig = go.Figure()

    for column in final.columns.to_list():
        fig.add_trace(
            go.Scatter(
                x = final.index,
                y = final[column],
                name = column
            )
        )
    
    # set only one line to be visible at all time
    buttons = []
    for ind, column in enumerate(final.columns.to_list()):
        temp = {}
        default_visible = [False] * len(final.columns)
        default_visible[ind] = True
        temp['label'] = column
        temp['method'] = 'update'
        temp['args'] = [{'visible': default_visible,
                         'title': column,
                          'showlegend': True}]
        buttons.append(temp)

    # add dropdown menu
    fig.update_layout(
        updatemenus=[go.layout.Updatemenu(
            bgcolor = '#e7dff0',
            active = 99,
            bordercolor = '#FFFFFF',
            font = dict(size=11, color='#000000'),
            buttons=buttons,
            showactive=False,
            x=0.1,
            xanchor="left",
            y=1.1,
            yanchor="top",
            ),
        ])  
    
    # add formatting
    fig.update_layout(xaxis_title = 'Date', yaxis_title = 'Channel Video Views')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
               margin=dict(l=10, r=10, t=10, b=10), showlegend = False, yaxis_showgrid=False, xaxis_showgrid = False)  #can add transition duration here
               
    return fig




# ========= Daily callbacks ==================
###################### Tab 1 Row 1 Charts
@app.callback(
    Output('categories_graph_daily', 'figure'),
    [Input('date_selector', 'value')])
    
def update_category_bar_daily(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] == value)]
    
    temp = filtered_df['categoryIdName'].value_counts().reset_index()
    fig = px.bar(temp, x="index", y="categoryIdName", text='categoryIdName', labels={'index': 'Categories', 'categoryIdName': 'Count of Videos'})
    fig.update_traces(texttemplate='%{text:.0d}', textposition='inside')  #can add textposition here (inside/outside)
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                      margin=dict(l=10, r=10, t=10, b=10), yaxis_showgrid=False) #can add transition duration here
    fig.update_yaxes(showticklabels=False)
    return fig


@app.callback(
    Output('top_rank_daily', 'children'),
    [Input('date_selector', 'value')])
    
def update_trending_table_daily(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] == value)]
    
    filtered_df = filtered_df[filtered_df['rank'] <= 10]
    filtered_df = filtered_df.sort_values('rank', ascending = True)
    filtered_df = filtered_df[['rank', 'title', 'thumbnail_link', 'view_count']]
    
    images_decoded_list = [] 
    # decode image to HTML to show in table
    for idx, elem in enumerate(filtered_df['thumbnail_link'].values):
        if elem != '':
            try:
                urllib.request.urlretrieve(elem, 'data/' + str(idx) + '.jpg')
                image_filename = 'data/' + str(idx) + '.jpg' # replace with your own image
            except:
                image_filename = 'data/test.jpg'
        else:
            image_filename = 'data/test.jpg' # replace with your own image
            
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())
        decoded_image = html.Img(src='data:image/jpg;base64,{}'.format(encoded_image.decode()))
        images_decoded_list.append(decoded_image)
    
    filtered_df['images'] = images_decoded_list    
    filtered_df = filtered_df[['rank', 'title', 'images', 'view_count']]
    filtered_df.columns = ['Rankings', 'Video Title', 'Thumbnail', 'Views']
    filtered_df['Views'] = filtered_df['Views'].apply(lambda x: str(round(x/1000000, 1)) + 'M')
    
    return dbc.Table.from_dataframe(filtered_df, bordered=True, responsive="sm", id="top_rank_daily_table")



############### Tab 1 Second Row Charts
@app.callback(
    Output('most_viewed_daily', 'figure'),
    [Input('date_selector', 'value')])
    
def update_viewed_bar_daily(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] == value)]
    
    filtered_df = filtered_df.sort_values('view_count', ascending = True)
    filtered_df = filtered_df[-10:]
    
    def shorten_title(x, num_chars):
        if len(x) < num_chars:
            return x
        
        if x == 'BLACKPINK - \'How You Like That\' M/V':
            return x[:num_chars-1] + '...1'
        else:
            return x[:num_chars] + '...' 

    filtered_df['title_short'] = filtered_df['title'].apply(lambda x: shorten_title(x, 20))

    fig = px.bar(filtered_df, x="view_count", y="title_short", text='view_count', 
                 hover_data={'view_count': ':.3s',
                             'title': True,
                             'title_short': False})
    fig.update_traces(texttemplate='%{text:.2s}', textposition='inside')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                   margin=dict(l=50, r=10, t=10, b=10), xaxis_showgrid=False) #can add transition duration here   # margin=dict(l=200, r=10, t=10, b=10),
    fig.update_yaxes(title='', automargin = True)
    return fig
    
@app.callback(
    Output('most_liked_daily', 'figure'),
    [Input('date_selector', 'value')])
    
def update_likes_bar_daily(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] == value)]
    
    filtered_df = filtered_df.sort_values('likes', ascending = True)
    filtered_df = filtered_df[-10:]
    
    def shorten_title(x, num_chars):
        if len(x) < num_chars:
            return x
        
        if x == 'BLACKPINK - \'How You Like That\' M/V':
            return x[:num_chars-1] + '...1'
        else:
            return x[:num_chars] + '...' 

    filtered_df['title_short'] = filtered_df['title'].apply(lambda x: shorten_title(x, 20))

    fig = px.bar(filtered_df, x="likes", y="title_short", text='likes', 
                 hover_data={'likes': ':.3s',
                             'title': True,
                             'title_short': False})
    fig.update_traces(texttemplate='%{text:.2s}', textposition='inside')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                   margin=dict(l=50, r=10, t=10, b=10), xaxis_showgrid=False) #can add transition duration here   # margin=dict(l=200, r=10, t=10, b=10),
    fig.update_yaxes(title='', automargin = True)
    return fig

@app.callback(
    Output('most_comment_daily', 'figure'),
    [Input('date_selector', 'value')])
    
def update_comment_bar_daily(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] == value)]
    
    filtered_df = filtered_df.sort_values('comment_count', ascending = True)
    filtered_df = filtered_df[-10:]
    
    def shorten_title(x, num_chars):
        if len(x) < num_chars:
            return x
        
        if x == 'BLACKPINK - \'How You Like That\' M/V':
            return x[:num_chars-1] + '...1'
        elif x == 'Tiara Andini - Maafkan Aku #TerlanjurMencinta (Official Music Video)':
            return x[:num_chars-1] + '...1'
        elif x == 'Ziva Magnolya - Tak Sanggup Melupa #TerlanjurMencinta (Official Music Video)':
            return x[:num_chars-1] + '...1'
        elif x == 'Lyodra - Mengapa Kita #TerlanjurMencinta (Official Music Video)':
            return x[:num_chars-1] + '...1'
        else:
            return x[:num_chars] + '...' 
    
    filtered_df['title_short'] = filtered_df['title'].apply(lambda x: shorten_title(x, 20))

    fig = px.bar(filtered_df, x="comment_count", y="title_short", text='comment_count', 
                 hover_data={'comment_count': ':.3s',
                             'title': True,
                             'title_short': False})
    fig.update_traces(texttemplate='%{text:.2s}', textposition='inside')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                   margin=dict(l=50, r=10, t=10, b=10), xaxis_showgrid=False) #can add transition duration here   # margin=dict(l=200, r=10, t=10, b=10),
    fig.update_yaxes(title='', automargin = True)
    return fig


########## Tab 1 Row 3 Charts
@app.callback(
    Output('trending_video_publish_daily', 'figure'),
    [Input('date_selector', 'value')])
    
def update_publish_day_daily(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] == value)]
    filtered_df = filtered_df.resample('D', on='publishedAt').count()['video_id'].reset_index()
    filtered_df.columns = ['Published Day', 'Count of Videos']
    filtered_df['color'] = '#636EFB'
    filtered_df.iloc[-1,2] = 'Yellow'
   
    fig = px.bar(filtered_df, x="Published Day", y="Count of Videos", text='Count of Videos', color = 'color', hover_data={'color': False})
    fig.update_traces(texttemplate='%{text:.0d}', textposition='inside')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
                   margin=dict(l=10, r=10, t=10, b=10), yaxis_showgrid=False, showlegend=False) #can add transition duration here   

    return fig


@app.callback(
    Output('published_hour_daily', 'figure'),
    [Input('date_selector', 'value')])
    
def update_publish_hour_bar_daily(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] == value)]
        
    def create_bins():
        ans = []
        for i in range(24):
            ans.append(str(i) + ':00')
            ans.append(str(i) + ':30')
        return ans
        
    bins = create_bins()
    count_bins = pd.DataFrame()
    count_bins['bins'] = bins

    temp = filtered_df.groupby(['publish_cat', 'categoryIdName']).agg('count')['title'].reset_index()
    # filter only top5 categories for the day
    top_5 = no_dups_f.groupby(['categoryIdName']).agg('count')['title'].reset_index()
    top_5 = top_5.sort_values('title', ascending = False)
    top_5 = top_5['categoryIdName'].values[:5]
    
    def map_others(x):
        if x not in top_5:
            return 'Others'
        else:
            return x
    # map categories not in top 5 into others
    temp['categoryIdName'] = temp['categoryIdName'].apply(lambda x: map_others(x)) 
    
    # put into appropriate format
    count_bins = pd.merge(count_bins, temp, left_on = 'bins', right_on = 'publish_cat', how = 'left')
    count_bins.drop(['publish_cat'], axis = 1, inplace = True)
    count_bins['title'] = count_bins['title'].fillna(0)
    count_bins['title'] = count_bins['title'].astype(int)
    count_bins = count_bins.groupby(['bins', 'categoryIdName']).agg('sum').reset_index()
    
    bins_pivot = count_bins.pivot(index='bins', columns='categoryIdName', values='title')
    bins_pivot = bins_pivot.reindex(bins)
        
    bins_pivot = bins_pivot.reset_index() 
    bins_pivot = bins_pivot.fillna(0)
    bins_pivot = bins_pivot.T.reset_index()
    
    # create stacked bar chart
    stacked_data = []
    for i in range(1, bins_pivot.shape[0]):
         stacked_data.append(go.Bar(name = bins_pivot.loc[i, 'categoryIdName'], x = bins, y = bins_pivot.iloc[i,:][1:].values)) 
    
    stacked_data = stacked_data[::-1]
    
    fig = go.Figure(data=stacked_data)
    # Change the bar mode
    fig.update_layout(barmode='stack', xaxis_title = 'Hour of Publish (WIB)', yaxis_title = 'Count of Videos')
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, 
               margin=dict(l=10, r=10, t=10, b=10), yaxis_showgrid=False) #can add transition duration here
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))

    return fig


########## Tab 1 Row 4 Charts
@app.callback(
    Output('top_channel_daily', 'children'),
    [Input('date_selector', 'value')])
    
def update_channel_table_daily(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] == value)]
        
    filtered_df = filtered_df.groupby(['channelTitle', 'avatar_url', 'channel_type','curr_subs']).agg('count')['video_id'].reset_index()
    filtered_df = filtered_df.sort_values('video_id', ascending = False)
    filtered_df = filtered_df[:10]
    
    images_decoded_list = [] 
    # decode image to HTML to show in table
    for idx, elem in enumerate(filtered_df['avatar_url'].values):
        if elem != '':
            urllib.request.urlretrieve(elem, 'data/' + str(idx) + '.jpg')
            image_filename = 'data/' + str(idx) + '.jpg' # replace with your own image
        else:
            image_filename = 'data/test.jpg' # replace with your own image
            
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())
        decoded_image = html.Img(src='data:image/jpg;base64,{}'.format(encoded_image.decode()))
        images_decoded_list.append(decoded_image)
    
    filtered_df['images'] = images_decoded_list    
    filtered_df.drop(['avatar_url'], axis = 1, inplace = True)
    filtered_df = filtered_df[['channelTitle', 'images', 'channel_type', 'curr_subs', 'video_id']]
    filtered_df.columns = ['Channel Title', 'Channel Avatar', 'Channel Category', 'Current Subscribers', 'Trending Videos Count']
    
    return dbc.Table.from_dataframe(filtered_df, bordered=True, responsive="sm", id="top_channel_daily_table")

@app.callback(
    Output('country_origin_channel_daily', 'figure'),
    [Input('date_selector', 'value')])
    
def update_country_origin_channel_daily(value = date_list[0]): 
    filtered_df = df[(df['trending_date'] == value)]
    
    code_mapping = {'AU': 'AUS', 'CN': 'CHN', 'DE': 'DEU', 'ES': 'ESP', 'GB': 'GBR','GH': 'GHA','ID': 'IDN', 'IE': 'IRL', 'IN': 'IND', 'IT': 'ITA',
                    'JP': 'JPN', 'KR': 'KOR', 'MY': 'MYS', 'RU': 'RUS', 'US': 'USA', 'VN': 'VNM'}
    
    filtered_df = filtered_df.groupby(['country']).agg('count')['video_id'].reset_index()
    filtered_df = filtered_df[filtered_df['country'] != '']
    filtered_df['iso_alpha'] = filtered_df['country'].apply(lambda x: code_mapping[x])
    filtered_df.columns = ['country', 'count_of_videos', 'iso_alpha']
    fig = px.choropleth(filtered_df, locations ="iso_alpha",
                        color="count_of_videos",
                        scope = 'world',
                        projection = 'natural earth',
                        range_color = (1,30))
    fig.update_layout(paper_bgcolor='#161a28', plot_bgcolor='#161a28', font_color = '#ffffff', autosize=True, geo=dict(bgcolor='#161a28'), margin=dict(l=10, r=10, t=10, b=10),
                      coloraxis_showscale=False)
    return fig


if __name__ == '__main__':
    #### Pick one of the two options
    # Default
    app.run_server(debug=True)
    
    # Deployment on Docker
    #app.run_server(
    #    host='0.0.0.0',  # For deployment! if not commented in local use localhost:8050 to access app.
    #    port=8050,
    #    debug=True
    #)
    
    