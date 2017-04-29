# Alamo Alerts Module

import requests
import json
import os
import arrow
import tweepy

from apscheduler.schedulers.blocking import BlockingScheduler

# define task scheduler
scheduledTask = BlockingScheduler()

@scheduledTask.scheduled_job('interval', minutes=5)
def alamoAlertGenerator():

    # define global vars (local time object)
    utcTime = arrow.utcnow()
    localTime = utcTime.to('US/Central')

    # define twitterbot with auth keys
    twitterAuth = tweepy.OAuthHandler("MzMGLR7WDxAVnFm1mfCwqqZ5c", "L7zzwuL7RWXL7FgXGOUlWDj83DdUGIl2JyM2zH4T3g19o3MnRa")
    twitterAuth.set_access_token("856950304725770240-AaDXJODlclQPVlGAhj5jo6PDS2jZSth", "KqV9NwRuRiN8iZ0Ha8LJ513QnUXaJnsbgpUFZ6XA8rMCK")
    twitterApi = tweepy.API(twitterAuth)
    
    # GET Alamo API
    alamoFeed = requests.get('http://feeds.drafthouse.com/adcService/showtimes.svc/market/0000/')
    alamoFeedJson = alamoFeed.json()
    # GET Storing JSON file
    with open("alamoDataStorage.json") as storageDataJson:
        storageData = json.load(storageDataJson)
        # print("-------------------------------")
        # print(storageData)
        # print("-------------------------------")

        # create a new writeable Storing JSON file which we will use to write new objects to and replace our old Storing JSON file if changes are made
        with open("alamoDataStorage-new.json", "w") as storageDataJsonNew:

            # json.dump(storageData, storageDataJsonNew)

            # set up a flag for each cinema we look at (this way we don't get tons of duplicates per date)
            cinemaTweetFlag0003 = 0
            # for each theater we look at, a tweet status string will be created
            twitterStatus0003 = ""

            # print('New Movies On Sale:')
            # for each 'Dates', do the following
            for date in alamoFeedJson["Market"]["Dates"]:
                # save the date for looking up additional times
                currentDate = date["DateId"]
                # filter data down to specific 'Cinemas'
                # look for 'CinemaId' "0003" or 'CinemaSlug' "village"
                for cinema in date["Cinemas"]:
                    # temporary condition so we look a the Village location specifically
                    if cinema["CinemaId"] == "0003":
                        
                        # print(cinema["CinemaName"] +" showings found for " + date["Date"] + ":")
                        for storageDataCinema in storageData["Cinemas"]:
                            if storageDataCinema["CinemaId"] == cinema["CinemaId"]:
                                currentStorageCinema = storageDataCinema
                                # print(currentStorageCinema)
                            else:
                                continue
                        # if new 'Films' exist (perform a search against the Storing JSON)
                        for film in cinema["Films"]:
                            # set up an 'undefined' object that gets over-written when we find non-matches in the Storing JSON
                            currentStorageFilm = {
                                "FilmSlug": "undefined"
                            }
                            # look through our current cinema storage and replace the undefined object if a match is found
                            for storageFilm in currentStorageCinema["Films"]:
                                if storageFilm["FilmSlug"] == film["FilmSlug"]:
                                    currentStorageFilm = storageFilm

                            # if no object replacements were done in the previous loop, we'll then check if we should add an additional time flag
                            if currentStorageFilm["FilmSlug"] != "undefined":
                                # ----------------------------------- #
                                # Additional Time Functionality Start #
                                # ----------------------------------- #
                                # for each 'Series' within 'Films'
                                for series in film["Series"]:
                                    # for each 'Formats' within 'Series'
                                    for seriesformat in series["Formats"]:
                                        # for each 'Sessions' within 'Formats'
                                        for session in seriesformat["Sessions"]:
                                            if currentStorageFilm["FilmOnSaleAddl"] == "false":
                                                # set up dates from the current lookup date as well as the Storage JSON 'FilmOnSaleDate'
                                                premiereDateFormatted = arrow.get(currentStorageFilm["FilmOnSaleDate"], 'YYYYMMDD')
                                                currentDateFormatted = arrow.get(currentDate, 'YYYYMMDD')
                                                dateDiff = 0
                                                newTimeFlag = 0

                                                # generate a simple number for day range
                                                for d in arrow.Arrow.range('day', premiereDateFormatted, currentDateFormatted):
                                                    dateDiff += 1

                                                # we'll also append any additional times in here if needed, but only if the showing is < 4 days from opening
                                                if (session["SessionTime"] not in currentStorageFilm["FilmShowtimes"]) and dateDiff < 4:
                                                    currentStorageFilm["FilmShowtimes"] += session["SessionTime"] + " "
                                                    newTimeFlag = 1

                                                # if the additional show flag for this movie is not flipped AND the new date is within 3 days of the opening date AND the movies name is not already contained in the tweet text (for brand new movies)
                                                if dateDiff > 1 and dateDiff < 4  and (film["FilmName"] not in twitterStatus0003) and newTimeFlag == 1:
                                                    currentStorageFilm["FilmOnSaleAddl"] = "true"
                                                    # here we'll also add a line item to the tweet for the 'new' film on sale
                                                    if cinemaTweetFlag0003 == 0:
                                                        twitterStatus0003 += "Now On Sale at "+ cinema["CinemaName"] +":"
                                                        cinemaTweetFlag0003 = 1
                                                    twitterStatus0003 += "\n- " + film["FilmName"] + " [Add'l Times]"
                                                continue
                                            else:
                                                continue
                                        # note: this may be 'continue' overkill but for now it helps run through the script much faster (too many nested for loops :/ )
                                        continue
                                    continue
                                # ----------------------------------- #
                                #  Additional Time Functionality End  #
                                # ----------------------------------- #
                                continue
                            else:

                                # print "- "+ film["FilmName"]
                                # create a temporary film object we will store in our db if needed
                                newFilmObj = {
                                    "FilmId": film["FilmId"],
                                    "FilmName": film["FilmName"],
                                    "FilmSlug": film["FilmSlug"],
                                    "FilmOnSale": "false",
                                    "FilmOnSaleAddl": "false",
                                    "FilmOnSaleDate": date["DateId"],
                                    "FilmShowtimes": ""
                                }

                                # for each 'Series'
                                for series in film["Series"]:
                                    # for each 'Formats'
                                    for seriesformat in series["Formats"]:
                                        # for each 'Sessions'
                                        for session in seriesformat["Sessions"]:
                                            if session["SessionStatus"] == "onsale":
                                                newFilmObj["FilmOnSale"] = "true"
                                                newFilmObj["FilmShowtimes"] += session["SessionTime"] + " "

                                                # before we append the new object lets first check again our current list of objs
                                                filmExistsFlag = 0
                                                for storageFilm in currentStorageCinema["Films"]:
                                                    if newFilmObj["FilmSlug"] == storageFilm["FilmSlug"]:
                                                        filmExistsFlag = 1
                                                        continue

                                                # write newFilmObj into object store
                                                if filmExistsFlag == 0:
                                                    currentStorageCinema["Films"].append(newFilmObj)
                                                    # here we'll also add a line item to the tweet for the 'new' film on sale
                                                    if cinemaTweetFlag0003 == 0:
                                                        twitterStatus0003 += "Now On Sale at "+ cinema["CinemaName"] +":"
                                                        cinemaTweetFlag0003 = 1
                                                    twitterStatus0003 += "\n- " + film["FilmName"]
                                                continue
                                            else:
                                                continue
                                        # note: this may be 'continue' overkill but for now it helps run through the script much faster (too many nested for loops :/ )
                                        continue
                                    continue
                                continue
                            continue

            # - if alert exists for this cinema, send twitter alert
            # - finally delete Alert Text object
            # TWITTER STATUS TEXT EXAMPLE:
            # "Multi-Line List:\n- Line Item 1\n- Line Item 2\n- Line Item 3\n- Line Item 4\n- Line Item 5\n- Line Item 6\n- Line Item 7\n- Line Item 8"
            if twitterStatus0003 != "":
                print twitterStatus0003
                twitterApi.update_status(twitterStatus0003)
            else:
                print "No new movies :("

            # - if any changes were made to it, PUT Storing API
            

            # then replace the original file with the new data
            storageData["Cinemas"] = []
            storageData["Cinemas"].append(currentStorageCinema)
            json.dump(storageData, storageDataJsonNew)

            # and replace the the old file with the new file
            os.renames("alamoDataStorage.json", "z_archive/alamoDataStorage-"+ localTime.format('YYYYMMDD') +".json")
            os.renames("alamoDataStorage-new.json", "alamoDataStorage.json")

scheduledTask.start()