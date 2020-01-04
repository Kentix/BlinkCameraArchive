# Protocol information from https://github.com/MattTW/BlinkMonitorProtocol
# Be sure to edit the username + password below, to match you account
# Usage Example: Blink_Video_Downloader.py

# Comments added by @Kentix on GitHub
import requests
import shutil
import os
import sys
import json
import time

from datetime import datetime, timedelta
import pytz

import os.path

username = "ENTER-BLINK-USERNAME-HERE"
password = "ENTER-BLINK-PASSWORD-HERE"
# This client specifier came from a mitmproxy in September 2019
client_specifier = "iPhone10,6 | 12.4.1 | 5.1.0 (5536) #e0b80286"

# Separator to be used for logging and printing output
separatorline = "---------------------------------------------"

timestr = time.strftime("%Y%m%d-%H%M%S")
logfile = timestr + '.log'
print("Log File Name:", logfile)

# Used for rudimentary logging


def logger(logtime, function, errstate, printedoutput):
    # logtime is the time the logger function was called
    print(separatorline)
    print(logtime)
    print(separatorline)
    # Function is the friendly name of the application function
    # pertaining to the logger invocation
    # i.e. "Downloading" OR "Logging" OR "Configuration"
    # OR "Authentication" etc.
    print(separatorline)
    print(function)
    print(separatorline)
    # errstate describes if the logged event is the result
    # of an error or success state
    print(separatorline)
    print(errstate)
    print(separatorline)
    # printedoutput prints the supplied output from the function
    # which is fed into the logger function
    print(separatorline)
    print(printedoutput)
    print(separatorline)

# Start bulding header for auth related HTTP requests
# The user-agent came from a mitmproxy in September 2019
headers = {
    'Host': 'prod.immedia-semi.com',
    'Content-Type': 'application/json',
    'user-agent': 'Blink/5536 CFNetwork/978.0.7 Darwin/18.7.0',
}
# Debug
print(separatorline)
print("Headers:", headers)
print(separatorline)

# Building payload to be sent for auth token
data = '{ "password" : "' + password + '", "client_specifier" : "' + \
    client_specifier + '", "email" : "' + username + '" }'
# Debug
print(separatorline)
print("Data:", data)
print(separatorline)

# Build the entire request post for the auth token
res = requests.post('https://rest.prod.immedia-semi.com/login',
                    headers=headers, data=data)

# Debug
print(separatorline)
print("Response:", res)
print(separatorline)

# Debug
print(separatorline)
print("Type:", type(res))
print(separatorline)

# Materialize an auth token for use in subsequent request headers
authToken = res.json()["authtoken"]["authtoken"]

# Used to send the request to the proper region
region = res.json()["region"]

# TBD
region = list(region.keys())[0]

# Show region
print(separatorline)
print("Region:", region)
print(separatorline)

# Show the auth token
print(separatorline)
print("Auth Token:", authToken)
print(separatorline)

# Reform header for use in subsequent requests
# with the newly minted auth token
headers = {
    'Host': 'prod.immedia-semi.com',
    'TOKEN_AUTH': authToken,
}

# Returned list of Blink networks associated with the account,
# returned by the auth request
network = res.json()["networks"]
# Blink account ID returned by the auth request
accountID = res.json()["account"]["id"]
# Show the account ID, for good measure I suppose
print(separatorline)
print("Blink Account ID:", accountID)
print(separatorline)

# Starting page number for returned/available mp4 assets
pageNum = 1

# Specify the naming format of the downloaded file,
# for example: 2019-08-11 14-55-22
fileFormat = "%Y-%m-%d_%H.%M.%S"

# Determines how far back assets should be downloaded, i.e. Now - 1 Day
deltatime = datetime.today() - timedelta(hours=24)
formatteddatetime = deltatime.strftime("%Y-%m-%d")
print(separatorline)
print("Time Span:", formatteddatetime)
print(separatorline)

while True:
    # Wait 1 second (unkown as to why, yet)
    time.sleep(1)
    # Materialize the URL using previously obtained 'REGION',
    # 'ACCOUNT ID' and 'PAGE NUM', note page num starts at '1'
    # You can change the date in the URL to one of your choice,
    # in the same format, this will retrieve all videos since
    # a provided date/time
    pageNumUrl = 'https://rest-' + region + \
                 '.immedia-semi.com/api/v1/accounts/' + \
                 str(accountID) + '/media/changed?since=' + \
                 formatteddatetime + 'T&page=' + str(pageNum)
    print(separatorline)
    print("Target URL:", pageNumUrl)
    print(separatorline)
    # Show the status and page number it is currently working on
    print(separatorline)
    print("## Processing page - " + str(pageNum) + " ##")
    print(separatorline)
    # Build the request given the built URL above and the header
    # with appropriate auth token intially obtained
    res = requests.get(pageNumUrl, headers=headers)
    # Store the json returned which contains the list of
    # video assets and related metadata
    videoListJson = res.json()["media"]
    # Determine? if a list of videos is not returned or empty (hence completed)
    if not videoListJson:
        # Show the status of the request, exclaiming completion!!!
        print(" * ALL DONE !! *")
        # Kill the if, when completed or no videos available
        break
    for videoJson in videoListJson:
        time.sleep(1)
        # print(json.dumps(videoJson, indent=4, sort_keys=True))
        # Build URL for each specified in the returned list
        mp4Url = 'https://rest-'+region+'.immedia-semi.com' + \
                 videoJson["media"]
        # Date/time manipulation?
        datetime_object = datetime.strptime(videoJson["created_at"],
                                            '%Y-%m-%dT%H:%M:%S+00:00')
        utcmoment = datetime_object.replace(tzinfo=pytz.utc)
        localDatetime = utcmoment.astimezone(
            pytz.timezone(videoJson["time_zone"])
            )
        # Build filename from info above
        fileName = localDatetime.strftime(fileFormat) + " - " + \
            videoJson["device_name"] + " - " + \
            videoJson["network_name"] + ".mp4"
        # Saving the mp4 to the local file system
        # TODO If the file is <2KB, dont bother writing it to the
        # filesystem? I'm not sure why these exist
        # but I think they are "deleted" from the app but
        # their metadata remains
        if os.path.isfile(fileName):
            print(" * Skipping " + fileName + " *")
        else:
            print("Saving - " + fileName)
            res = requests.get(mp4Url, headers=headers, stream=True)
            with open("tmp-download", 'wb') as out_file:
                shutil.copyfileobj(res.raw, out_file)
            os.rename("tmp-download", fileName)
    # Go to the next page of returned media assets
    # Note the max of returned assets in my case was "25"
    pageNum += 1
    # TODO Send notification email/pushbullet/sms or otherwise that this
    # has completed and the associated status
