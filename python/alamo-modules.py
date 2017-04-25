# Alamo Alerts Module

import requests
import json
import os
import arrow
# import tweepy

# for later when we come up with multiple python functions
# def generateAlamoAlerts():

# define global vars (local time object)
utcTime = arrow.utcnow()
localTime = utcTime.to('US/Central')
    
# GET Alamo API
alamoFeed = requests.get('http://feeds.drafthouse.com/adcService/showtimes.svc/market/0000/')
alamoFeedJson = alamoFeed.json()
# GET Storing API
with open("alamoDataStorage-"+ localTime.format('YYYYMMDD') +".json") as storageDataJson:
    storageData = json.load(storageDataJson)
    print("-------------------------------")
    print(storageData)
    print("-------------------------------")

    with open("alamoDataStorage-"+ localTime.format('YYYYMMDD') +"-new.json", "w") as storageDataJsonNew:

        # json.dump(storageData, storageDataJsonNew)

        print('New Movies On Sale:')
        # for each 'Dates', do the following
        for date in alamoFeedJson["Market"]["Dates"]:
            # filter data down to specific 'Cinemas'
            # look for 'CinemaId' "0003" or 'CinemaSlug' "village"
            for cinema in date["Cinemas"]:
                if cinema["CinemaId"] == "0003":
                    # print(cinema["CinemaName"] +" showings found for " + date["Date"] + ":")
                    for storageDataCinema in storageData["Cinemas"]:
                        if storageDataCinema["CinemaId"] == cinema["CinemaId"]:
                            currentStorageCinema = storageDataCinema
                            # print(currentStorageCinema)
                        else:
                            continue
                    # if new 'Films' exist (perform a search against the Storing API)
                    for film in cinema["Films"]:

                        currentStorageFilm = {
                            "FilmSlug": "undefined"
                        }

                        for storageFilm in currentStorageCinema["Films"]:
                            if storageFilm["FilmSlug"] == film["FilmSlug"]:
                                currentStorageFilm = storageFilm

                        if currentStorageFilm["FilmSlug"] != "undefined":
                            # if currentStorageFilm["FilmOnSaleAddl"] == "false":

                            # print film["FilmName"] + " already exists"
                            # we'll add in the 'additional time' functionality later
                            #     - for each existing 'Films' in the Storing API search, if 'FilmOnSaleAddl' == false && ('FilmOnSaleDate' + 4 days) > 'DateId'
                            #         - for each 'Series'
                            #             - for each 'Formats'
                            #                 - for each 'Sessions'
                            #                     - if session is new && 'SessionStatus' == "onsale", add Film to ALERT TEXT ARRAY
                            #                         - format: {{ FilmName }} [Add'l Times]
                            #                     - and set 'FilmOnSaleAddl' to true
                            #                     >> MOVE TO NEXT FILM
                            continue
                        else:
                            print "- "+ film["FilmName"]
                            newFilmObj = {
                                "FilmId": film["FilmId"],
                                "FilmName": film["FilmName"],
                                "FilmSlug": film["FilmSlug"],
                                "FilmOnSale":"false",
                                "FilmOnSaleAddl":"false",
                                "FilmOnSaleDate":date["DateId"]
                            }

                            #print newFilmObj


                            # for each 'Series'
                            for series in film["Series"]:
                                # for each 'Formats'
                                for seriesformat in series["Formats"]:
                                    # for each 'Sessions'
                                    for session in seriesformat["Sessions"]:
                                        if session["SessionStatus"] == "onsale":
                                            newFilmObj["FilmOnSale"] = "true"

                                            # write newFilmObj into 
                                            currentStorageCinema["Films"].append(newFilmObj)
                                            continue
                                        else:
                                            #currentStorageCinema["Films"].append(newFilmObj)
                                            continue
                                    continue
                                continue



                            continue

                        continue

        #                     - if 'SessionStatus' == "onsale", add Film to ALERT TEXT ARRAY
        #                         - format: {{ FilmName }}
        #                     - create new 'Films' object in Storing API
        #                     - and set 'FilmOnSale' to true
        #                     - and set 'FilmOnSaleDate' to 'DateId'
        #                     >> MOVE TO NEXT FILM

        # - if any changes were made to it, PUT Storing API
        # - if alerts exist, send twitter alert
        # - finally delete Alert Text object

        # then replace the original file with the new data
        storageData["Cinemas"] = []
        storageData["Cinemas"].append(currentStorageCinema)
        json.dump(storageData, storageDataJsonNew)

        # and replace the the old file with the new file
        # os.remove("alamoDataStorage-"+ localTime.format('YYYYMMDD') +".json")
        # os.renames("alamoDataStorage-"+ localTime.format('YYYYMMDD') +"-new.json", "alamoDataStorage-"+ localTime.format('YYYYMMDD') +".json")


