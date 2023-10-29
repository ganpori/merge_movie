import http.client
import httplib2
import os
from pathlib import Path
import pickle
import random
import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

"""
公式サンプルページ:https://developers.google.com/youtube/v3/guides/uploading_a_video?hl=ja
一番上に出てくる一通りそのまま説明してるところ:https://qiita.com/ny7760/items/5a728fd9e7b40588237c
oauth2clientは非推奨なのでgoogle-authを使おうというやつ:https://dev.classmethod.jp/articles/oauth2client-is-deprecated/
google-authでapiの認証を通す公式の例:https://developers.google.com/sheets/api/quickstart/python?hl=ja#step_3_set_up_the_sample
"""

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google API Console at
# https://console.cloud.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def get_authenticated_service():
    # サーバーアプリでoauthするためのgoogle公式説明
    # https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps?hl=ja#python

    #　oauthの説明、リフレッシュトークン、アクセストークン
    # https://logmi.jp/tech/articles/325886  oauthの概要
    # https://logmi.jp/tech/articles/325887　認可フローの説明
    # https://logmi.jp/tech/articles/325888  リフレッシュトークンの説明

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:  # credsがNoneの場合でもorで先にnot credsが評価されるからcreds.validが存在しなくてもよい
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(e)
                # refreshに失敗したらとりあえずcredsを作り直す。oauthよくわからんからとりあえずこう。
                # oauth本読んで少しでもわかったらちゃんとリフレッシュする方法作りたい。
                print("credsを作り直す")
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE,
                    scopes=YOUTUBE_UPLOAD_SCOPE,
                )
                creds = flow.run_local_server(port=0)

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=YOUTUBE_UPLOAD_SCOPE,
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        credentials=creds,
    )


def _get_latest_mp4_path():
    path_data_dir = Path(".")
    list_path_mp4 = [path.absolute() for path in path_data_dir.glob("*.mp4")]
    list_path_mp4.sort()
    path_mp4_latest = list_path_mp4[-1]
    return path_mp4_latest


def initialize_upload(youtube, path_upload_file):
    # argparser.add_argument("--file", required=True, help="Video file to upload")
    # argparser.add_argument("--title", help="Video title", default="Test Title")
    # argparser.add_argument(
    #     "--description", help="Video description", default="Test Description"
    # )
    # argparser.add_argument(
    #     "--category",
    #     default="22",
    #     help="Numeric video category. "
    #     + "See https://developers.google.com/youtube/v3/docs/videoCategories/list",
    # )
    # argparser.add_argument(
    #     "--keywords", help="Video keywords, comma separated", default=""
    # )
    # argparser.add_argument(
    #     "--privacyStatus",
    #     choices=VALID_PRIVACY_STATUSES,
    #     default=VALID_PRIVACY_STATUSES[0],
    #     help="Video privacy status.",
    # )
    # args = argparser.parse_args()

    # if not os.path.exists(args.file):
    #     exit("Please specify a valid file using the --file= parameter.")
    body = dict(
        snippet=dict(
            title=path_upload_file.stem,
            description="",
            categoryId=17,  # 17はsports
        ),
        status=dict(
            privacyStatus=VALID_PRIVACY_STATUSES[0],  # public
        ),
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(
            filename=path_upload_file.as_posix(), chunksize=-1, resumable=True
        ),
    )

    resumable_upload(insert_request)


# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if "id" in response:
                    print("Video id '%s' was successfully uploaded." % response["id"])
                else:
                    exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (
                    e.resp.status,
                    e.content,
                )
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2**retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)


def main(path_upload_file=None):
    if path_upload_file is None:  # 引数なかったら適当に最新の動画取得する
        path_upload_file = _get_latest_mp4_path()
    print(f"start upload {path_upload_file}")
    youtube = get_authenticated_service()
    try:
        initialize_upload(youtube, path_upload_file=path_upload_file)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    return


if __name__ == "__main__":
    main()
