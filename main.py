"""_summary_
Main file of YTSA flask app
Routes for each page are defined as well as boilerplate setup.
"""
import os
import requests
import flask
from flask import redirect, session
from dotenv import find_dotenv, load_dotenv
# Local Imports
from YTSA_Core_Files import sql_admin_functions, sql_requests
from YTSA_Core_Files import sql_models as sqm
from YTSA_Core_Files.db import db
from vader import sent_score, ave_sent_score

load_dotenv(find_dotenv())
APIKEY = os.getenv("APIKEY")

def create_app(database, testing=False):
    """_summary_

    Returns:
        flask app: app object with settings
    """
    new_app = flask.Flask(__name__)
    new_app.config['TESTING'] = testing
    new_app.config.update(SECRET_KEY='12345')  # Key required for flask.session
    new_app.config["SQLALCHEMY_DATABASE_URI"] = database
    db.init_app(app)
    with new_app.app_context():
        db.create_all()

    return new_app


PRODUCTION_DB = "sqlite:///YT_Sentiment_App.db"
app = create_app(PRODUCTION_DB)
# Create tabels if empty


@app.route('/')
def index():
    """_summary_
    Route to base page of website
    """
    # Set default username if has not logged in yet to guest for display.
    if not session:
        session['user'] = 'Guest'

    # sql_admin_functions.sql_add_demo_data_random(db, 20)
    return flask.render_template(
        "index.html",
    )


@app.route('/login', methods=["GET", "POST"])
def login_page():
    """_summary_
    Route to bare login page for testing
    (will remove later in favor of popup)
    """
    message = "Welcome to the YTSA!"

    if flask.request.method == "POST":
        form_data = flask.request.form
        # Get pass string entered into form
        db_user = None
        password_entered = form_data["password"]
        try:
            # Attempt to get user name from table,
            # if not result in failure and display message
            db_user = db.session.execute(db.select(sqm.Users).filter_by(
                user_name=form_data["user_name"])).scalar_one()
            # If user is found in DB compare entered password to
            # what is stored to validate (after decrypting)
            success = sql_admin_functions.validate_login(db_user, password_entered)
            # Add retreived username to sessoin
            session['user'] = db_user.user_name
            # Manually set modified to true
            session.modified = True
        except AttributeError:
            print("User not found in table")
            success = False

        # Send update with username for message or redirect back to main page
        # Else update message to reflect bad lgin.
        if success:
            return redirect("/", code=302)

        message = "Invalid login credentials"

    return flask.render_template(
        "login.html",
        login_message=message
    )


# this function is for converting large number of likes,
# comments and subscribers to 1.4K or 2.5M
def number_suffix(number):
    """_summary_
    # suffixes i.e million = m or thousand = K
    Args:
        number (_type_): _description_

    Returns:
        _type_: _description_
    """
    suffixes = ['', 'K', 'M', 'B', 'T']
    index_suffix = 0
    while number >= 1000 and index_suffix < len(suffixes) - 1:
        number /= 1000.0
        index_suffix += 1
    return f"{number:,.1f}{suffixes[index_suffix]}"


@app.route('/search_results', methods=["GET", "POST"])
def search_results():
    """_summary_
    Route to search results page
    """
    max_result = 6
    vid_dict = {
        "video_id": [],
        "video_title": [],
        "video_thumbnail": [],
        "channel_id": [],
        "channel_title": [],
        "channel_thumbnail": [],
        "channel_subscriber_count": []
    }

    form_data = flask.request.args

    query = form_data.get("term", "")

    search_url = "https://www.googleapis.com/youtube/v3/search?"
    search_params = {
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": max_result,
        "key": APIKEY

    }
    response_search = requests.get(search_url, search_params, timeout=30)
    response_search = response_search.json()

    for i in range(max_result):

        try:
            vid_dict["channel_id"].append(
                response_search["items"][i]['snippet']['channelId'])
        except IndexError:
            print("no channelid")

        try:
            vid_dict["video_id"].append(
                response_search["items"][i]['id']['videoId'])
        except IndexError:
            print("no videoid")
        try:
            vid_dict["video_title"].append(
                response_search["items"][i]['snippet']['title'])
        except IndexError:
            print("no videotitle")
        try:
            vid_dict["video_thumbnail"].append(
                response_search["items"][i]['snippet']['thumbnails']['high']['url'])
        except IndexError:
            print("no video thumbnail")

    print(vid_dict["channel_id"])

    channel_url = "https://www.googleapis.com/youtube/v3/channels?"
    channel_params = {
        "id": ','.join(vid_dict["channel_id"]),
        "part": "snippet, statistics",
        "key": APIKEY,

    }
    response_channel = requests.get(channel_url, channel_params, timeout=30)
    print(response_channel.text)

    response_channel = response_channel.json()

    for i in range(len(vid_dict["channel_id"])):
        try:
            vid_dict["channel_title"].append(
                response_channel["items"][i]['snippet']['title'])
        except IndexError:
            vid_dict["channel_title"].append("no title")

        try:
            vid_dict["channel_thumbnail"].append(
                response_channel["items"][i]['snippet']['thumbnails']['default']['url'])
        except IndexError:
            vid_dict["channel_thumbnail"].append("no thumbnail")

        try:
            vid_dict["channel_subscriber_count"].append(
                number_suffix(
                    float(
                        response_channel["items"][i]['statistics']['subscriberCount'])))
        except IndexError:
            vid_dict["channel_subscriber_count"].append("no subscriber")

    return flask.render_template(
        "search_results.html",
        videoId=vid_dict["video_id"],
        videoTitle=vid_dict["video_title"],
        channelId=vid_dict["channel_id"],
        videoThumbnail=vid_dict["video_thumbnail"],
        channelTitle=vid_dict["channel_title"],
        channelThumbnail=vid_dict["channel_thumbnail"],
        channelsubscriberCount=vid_dict["channel_subscriber_count"],

    )


@app.route('/video_view/', methods=["GET", "POST"])
def video_view():
    # pylint: disable=too-many-statements
    """_summary_
    Route to Video view page
    """
    max_comments = 100

    vid_dict = {
        "video_title": [],
        "channel_title": [],
        "subscriber_count": [],
        "comment_count": [],
        "like_count": "",
        "channel_thumbnail": [],
        "channelsub_scriber_count": [],
        "channel_id": [],
        "author_display_name": [],
        "author_profile_image_url": [],
        "text_display": [],
        "sent_scores": [],
        "ave_sent_scores": []
    }


    form_data = flask.request.args
    # print("\n\n\n")
    # print(form_data)
    # print("\n\n\n")
    query = form_data.get("watch?v", "")
    # print(query)

    video_url = "https://www.googleapis.com/youtube/v3/videos?"
    video_params = {
        "id": query,
        "part": 'snippet, statistics',
        "type": "video",
        "key": APIKEY,

    }
    response_video = requests.get(video_url, video_params, timeout=30)
    response_video = response_video.json()

    try:
        vid_dict["video_title"] = response_video["items"][0]['snippet']['title']
    except KeyError:
        print("no title")

    try:
        vid_dict["channel_id"] = response_video["items"][0]['snippet']['channelId']
    except KeyError:
        print("no channelid")

    try:
        vid_dict["comment_count"] = number_suffix(float(
            response_video["items"][0]['statistics']['commentCount']))
    except KeyError:
        print("")

    try:
        vid_dict["like_count"] = number_suffix(float(
            response_video["items"][0]['statistics']['likeCount']))
    except KeyError:
        print("")

    channel_url = "https://www.googleapis.com/youtube/v3/channels?"
    channel_params = {
        "id": vid_dict["channel_id"],
        "part": "snippet, statistics",
        "key": APIKEY,

    }
    response_channel_vid = requests.get(channel_url, channel_params, timeout=30)
    print(response_channel_vid.text)
    response_channel_vid = response_channel_vid.json()

    try:
        vid_dict["channel_title"] = response_channel_vid["items"][0]['snippet']['title']
    except KeyError:
        print("no title")

    try:
        vid_dict["channel_thumbnail"] = response_channel_vid["items"][0]\
            ['snippet']['thumbnails']['default']['url']
    except KeyError:
        print("no thumbnail")

    try:
        vid_dict["channelsub_scriber_count"] = number_suffix(float(
            response_channel_vid["items"][0]['statistics']['subscriberCount']))
    except KeyError:
        print("no subscriber")

    comments_url = "https://www.googleapis.com/youtube/v3/commentThreads?"
    comments_params = {
        "videoId": query,
        "part": "snippet",
        "key": APIKEY,
        "maxResults": max_comments,
        "textFormat": 'plainText',
        "order": 'relevance'

    }
    response_comments = requests.get(comments_url, comments_params, timeout=30)
    # print(responseComments.text)
    response_comments = response_comments.json()

    for i in range(max_comments):

        try:
            vid_dict["author_profile_image_url"].append(
                response_comments["items"][i]['snippet']['topLevelComment']\
                    ['snippet']['authorProfileImageUrl'])
        except IndexError:
            print("no profile")

        try:
            vid_dict["author_display_name"].append(
                response_comments["items"][i]['snippet']['topLevelComment'][
                    'snippet']['authorDisplayName'])
        except IndexError:
            print("no author")

        try:
            vid_dict["text_display"].append(\
               response_comments["items"][i]['snippet']['topLevelComment']\
                   ['snippet']['textDisplay'])
            vid_dict["sent_scores"].append(
                sent_score(
                    response_comments["items"][i]['snippet']['topLevelComment']\
                        ['snippet']['textDisplay']))
        except IndexError:
            print("")

    ave_sent_scores = ave_sent_score(vid_dict["text_display"])
    # print(textDisplay)
    # print(authorDisplayname)

    return flask.render_template(
        "video_view.html",
        videoId=query,
        videoTitle=vid_dict["video_title"],
        subscriberCount=vid_dict["subscriber_count"],
        commentCount=vid_dict["comment_count"],
        likeCount=vid_dict["like_count"],
        channelThumbnail=vid_dict["channel_thumbnail"],
        channelsubscriberCount=vid_dict["channelsub_scriber_count"],
        channelId=vid_dict["channel_id"],
        channelTitle=vid_dict["channel_title"],
        authorDisplayname=vid_dict["author_display_name"],
        authorProfileImageUrl=vid_dict["author_profile_image_url"],
        textDisplay=vid_dict["text_display"],
        sent_score=vid_dict["sent_scores"],
        ave_sent_score=ave_sent_scores
    )


@app.route('/sql', methods=["GET", "POST"])
def sql_playground_temporary():
    """_summary_
    Route to SQL Demo Page
    """
    if flask.request.method == "POST":
        form_data = flask.request.form
        target_row = db.session.execute(db.select(sqm.VideoInfo).filter_by(
            id=form_data["video_id"])).scalar_one()
        # target_row.sentiment_score_average=form_data["new_score"]
        sql_requests.update_sentiment_average_video(
            target_row, float(form_data["new_score"]))
        db.session.commit()

    vids = sqm.VideoInfo.query.all()
    num_vids = len(vids)
    return flask.render_template(
        "sql_playground_temporary.html",
        num_vids=num_vids,
        vids=vids
    )


app.run(
    use_reloader=True,
    debug=True
)
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Runing Main.py')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
