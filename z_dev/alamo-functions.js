'use strict';
function showtimeController($scope, $http, $log, $timeout, FoundationApi, ModalFactory, $sce) {
  $scope.dataLoaded = false;
  $scope.dataError = false;
  var processFeed = function (feedUrl, cbSuccess) {
    $log.info("feedUrl [" + feedUrl + "]");
    $http.get(feedUrl).then(
      function(response) {    //success
        $log.info("feed loaded");
        if(response.data == null){
          $log.info("feed empty (null)");
          $scope.dataLoaded = true;
        }
        else
          cbSuccess(response.data,
            function(){
              $log.info("feed processed");
              $scope.dataLoaded = true;
            });
      },
      function(response){  //error
        $log.error("error code: "+response.number+" url: "+feedUrl);
        $scope.dataError = true;
      }
    );
  }

  var getContentFeed = function (filmSlug, cbSuccess) {
    $http.get('https://drafthouse.com/api/v1/shows/' + filmSlug).then(
      function(response) {    //success
        cbSuccess(response.data);
      },
      function(response){  //error
        $log.error("error code: "+response.number);
        $scope.dataError = true;
      }
    );
  }

  $scope.initMarket = function (feedBaseUrl,marketId) {
    $log.info("marketId [" + marketId + "]");
    processFeed(feedBaseUrl+'market/'+marketId+'/',
      function (data, cb) {
        $scope.showtimeDates = data.Market.Dates;
        $scope.selectedDate = $scope.showtimeDates[0];
        cb();
      }
    );
  }

  $scope.initCinema = function (feedBaseUrl,cinemaId) {
    var marketId = cinemaId.substring(0,2)+'00';
    $log.info("marketId [" + marketId + "]");
    $log.info("cinemaId [" + cinemaId + "]");

    processFeed(feedBaseUrl+'market/' + marketId + '/',
      function (data, cb) {
        var dates = data.Market.Dates;
        for(var d = dates.length-1; d >= 0 ; d--) {
          var keepDate = false;
          for (var c = dates[d].Cinemas.length-1; c >= 0; c--) {
            if (dates[d].Cinemas[c].CinemaId == cinemaId)
              keepDate = true;
            else
              dates[d].Cinemas.splice(c,1);
          }
          if (!keepDate) dates.splice(d,1);
        }
        $scope.showtimeDates = dates;
        $scope.selectedDate = $scope.showtimeDates[0];
        cb();
      }
    );
  }

  $scope.initFilm = function(feedBaseUrl,marketId,filmId) {
    $scope.filmId = filmId;
    $log.info("marketId [" + marketId + "]");
    $log.info("filmId [" + filmId + "]");

    filmId = filmId.split(',');

    processFeed(feedBaseUrl+'market/'+marketId+'/',
      function (data, cb) {
        var dates = data.Market.Dates;
        for(var d = dates.length-1; d >= 0 ; d--) {
          var keepDate = false;
          for (var c = dates[d].Cinemas.length-1; c >= 0; c--) {
            var keepCinema = false;
            for (var f = dates[d].Cinemas[c].Films.length-1; f >= 0 ; f--) {
              //if (dates[d].Cinemas[c].Films[f].FilmId == filmId){
              if (filmId.indexOf(dates[d].Cinemas[c].Films[f].FilmId) >= 0){
                keepCinema = true;
                keepDate = true;
              }
              else
                dates[d].Cinemas[c].Films.splice(f,1);
            }
            if (!keepCinema) dates[d].Cinemas.splice(c,1);
          }
          if (!keepDate) dates.splice(d,1);
        }
        $scope.showtimeDates = dates;
        $scope.selectedDate = $scope.showtimeDates[0];
        cb();
      }
    );
  }

  /*
   *  This function gets all of the sessions with the passed in parameters
   *   and saves them in $scope.filmsByAttribute
   */
  $scope.initAttribute = function(feedBaseUrl,marketId,attributes) {

    // clean up the attribute data to an array of strings
    attributes = _.filter(_.split(attributes, ','), function(attribute) {
      return !_.isEmpty(_.trim(attribute));
    });

    // get the feed for the market
    processFeed(feedBaseUrl+'market/'+marketId+'/', function (data, cb) {
      var dates = data.Market.Dates;
      var attributeFilms = [];

      // Flattening feed structure
      var showings = _.flatMap(dates, function(date) {
        return _.flatMap(date.Cinemas, function(cinema) {
          return _.flatMap(cinema.Films, function(film) {
            return _.flatMap(film.Series, function(series) {
              return _.flatMap(series.Formats, function(format) {
                return _.flatMap(format.Sessions, function(session) {
                  return {
                    session: session,
                    film: film,
                    cinema: cinema,
                    date: date
                  };
                })
              })
            })
          })
        })
      });

      // Filter out showings without matching attributes
      showings = _.filter(showings, function(showing) {
        var showingAttributes = _.flatMap(showing.session.Attributes, 'AttributeId');
        return !_.isEmpty(_.intersection(attributes, showingAttributes));
      });

      // Sort showings so they are displayed in the right order
      showings = _.sortBy(showings, ['date.DateId', 'cinema.CinemaName']);

      // Group showings to display the showings by film
      var showingsByFilm = _.groupBy(showings, 'film.FilmName');

      // Group each film by date and theatre
      _.forEach(showingsByFilm, function(data, film) {
        showingsByFilm[film] = _.groupBy(data, 'date.Date');
        _.forEach(showingsByFilm[film], function(filmData, date){
          showingsByFilm[film][date] = _.groupBy(filmData, 'cinema.CinemaName');
        });
      });

      $scope.showingsByFilm = showingsByFilm;
      $scope.getPostersForMovies();
    });
  };

  $scope.getPostersForMovies = function() {
    _.forEach($scope.showingsByFilm, function(data, film) {
      _.forEach($scope.showingsByFilm[film], function(dateData, date) {
        _.forEach($scope.showingsByFilm[film][date], function(cinemaData2, cinema2) {
          $scope.showingsByFilm[film].Slug = $scope.showingsByFilm[film][date][cinema2][0].film.FilmSlug;
        });
      });
      getContentFeed($scope.showingsByFilm[film].Slug, function (content, cb) {
        $scope.showingsByFilm[film].Poster = content.data.poster;
      });
    });
    $scope.dataLoaded = true;
  }

  //$scope.$watch("calendarCinema", function (newValue, oldValue) {
  //  $timeout(function() {
  //    $(document).foundation();
  //    $log.info("refoundation");
  //  });
  //});


  $scope.initCalendar = function (feedBaseUrl,cinemaId) {
    $log.info("cinemaId [" + cinemaId + "]");
    processFeed(feedBaseUrl+'calendar/'+cinemaId+'/',
      function (data, cb) {
        $scope.calendarCinema = data.Calendar.Cinemas[0];
        cb();
        $timeout(function() {
          $(document).foundation();
          $log.info("refoundation !!!");
        });
      }
    );
  }



  $scope.sessionClicked = function (session,format,series,film,cinema) {
    $log.info("Session Clicked");
    session.format = format;
    session.series = series;
    session.cinema = cinema;
    session.film = film;

    if (session.SessionStatus == 'onsale' || session.SessionStatus == 'low') {
      session.seatPreviewURL = $sce.trustAsResourceUrl('https://drafthouse.com/tickets/seatpreview/'+session.SessionId+'/'+session.cinema.CinemaId);
    } else {
      session.seatPreviewURL = '';
    }

    if(session.Attributes && session.film.FilmAgePolicy != "")
      for(var a = 0; a<session.Attributes.length; a++)
        if(session.Attributes[a].AttributeId == "BD" || session.Attributes[a].AttributeId == "AA" || session.Attributes[a].AttributeId == "A4A" || session.Attributes[a].AttributeId == "AFA")
          session.film.FilmAgePolicy = "";

    session.ticketUri = session.cinema.MarketSlug+"/tickets/"+session.film.FilmSlug+"/tickets/"+session.cinema.CinemaId+"_"+session.SessionId;

    $log.info(session);

    var sessionModal = new ModalFactory({
      class: 'medium',
      overlay: true,
      overlayClose: true,
      templateUrl: 'sessionModal',
      contentScope: {
        close: function() {
          sessionModal.deactivate();
          $timeout(function() {
            sessionModal.destroy();
          }, 1000);
        },
        sSession: session
      }
    });

    sessionModal.activate();
  }

};

function loginController($scope, $http, $interval, $timeout) {

    $scope.popup = $.magnificPopup.instance;

    $scope.signInOauth = function(provider) {
        var url = '/?ACT=290&service=' + provider;

        var popupWindow = $scope.popup(url, {
            resizable: 1,
            scrollbars: 1,
            width: 500,
            height: 550
        });

        var promise = $interval(function() {
            if (popupWindow.closed) {
                $http.get('/ajax/.is-logged-in')
                    .then(function(response) {
                        if (response.data == 'yes') {
                            $scope.replaceAccount();
                        }
                    });
                $interval.cancel(promise);
            }
        }, 500);
    };

    $scope.signInEmail = function(url) {
        $scope.magnificPopup = $.magnificPopup.open({
            items: {
                src: url
            },
            type: 'iframe'
        });

        $scope.magnificPopup = $.magnificPopup.instance;

        var promise = $interval(function() {
            $http.get('/ajax/.is-logged-in')
                .then(function(response) {
                    if (response.data == 'yes') {
                        $scope.magnificPopup.close();
                        $interval.cancel(promise);
                        $scope.replaceAccount();
                    }
                    // $interval.cancel(promise);
                });
        }, 2000);
    };

    $scope.replaceAccount = function() {
        $http.get('/partials/.account').then(function(response) {
            angular.element('.victory-block').html(response.data);
        });
    };

    $scope.closeWindow = function() {
    };

    $scope.popup = function(url, options) {
        var documentElement = document.documentElement;

        // Multi Screen Popup Positioning (http://stackoverflow.com/a/16861050)
        // Credit: http://www.xtf.dk/2011/08/center-new-popup-window-even-on.html
        // Fixes dual-screen position                         Most browsers      Firefox

        if (options.height) {
            var dualScreenTop = window.screenTop !== undefined ? window.screenTop : screen.top;
            var height = screen.height || window.innerHeight || documentElement.clientHeight;
            options.top = parseInt((height - options.height) / 2, 10) + dualScreenTop;
        }

        if (options.width) {
            var dualScreenLeft = window.screenLeft !== undefined ? window.screenLeft : screen.left;
            var width = screen.width || window.innerWidth || documentElement.clientWidth;
            options.left = parseInt((width - options.width) / 2, 10) + dualScreenLeft;
        }

        // Convert options into an array
        var optionsArray = [];
        Object.keys(options).forEach(function(name) {
            var value = options[name];
            optionsArray.push(name + (value !== null ? '=' + value : ''));
        });

        // Call the open() function with the initial path
        //
        // OAuth redirect, fixes URI fragments from being lost in Safari
        // (URI Fragments within 302 Location URI are lost over HTTPS)
        // Loading the redirect.html before triggering the OAuth Flow seems to fix it.
        //
        // Firefox  decodes URL fragments when calling location.hash.
        //  - This is bad if the value contains break points which are escaped
        //  - Hence the url must be encoded twice as it contains breakpoints.
        // if (navigator.userAgent.indexOf('Safari') !== -1 && navigator.userAgent.indexOf('Chrome') === -1) {
        //     url = redirectUri + '#oauth_redirect=' + encodeURIComponent(encodeURIComponent(url));
        // }

        var popup = window.open(
            url,
            '_blank',
            optionsArray.join(',')
        );

        if (popup && popup.focus) {
            popup.focus();
        }

        return popup;
    }
};

angular
    .module('drafthouseShowtimes', ['ui.router','ngAnimate','foundation','foundation.dynamicRouting','foundation.dynamicRouting.animations', 'angular.truncate'])
    .controller('ShowtimeController', showtimeController)
    .controller('OauthController', loginController)
  ;

