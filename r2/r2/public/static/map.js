(function ($) {
  /* Show Meetup map */
  window.createMap = function (map) {
    if (map) {
      loadMaps(function() { 
        var markers = $('.marker', map);
        var myOptions = {
          zoom: 12,
          mapTypeId: google.maps.MapTypeId.ROADMAP
        };
        var gMap = new google.maps.Map(map, myOptions);

        var first;
        var bounds = new google.maps.LatLngBounds();

        markers.each(function(i,m) {
          var lat = $(m).attr('data-latitude');
          var lng = $(m).attr('data-longitude');
          latlng = new google.maps.LatLng(lat, lng);
          bounds.extend(latlng);
          if (!first)
            first = latlng;
          var marker = new google.maps.Marker({
            map: gMap,
            draggable: false,
            animation: google.maps.Animation.DROP,
            position: latlng,
            title: $(m).attr('data-title')
          });
          var url = $(m).attr('data-url');
          if (url) {
            google.maps.event.addListener(marker, 'click', function() {
              window.location.href = url;
            });
          }
        });

        /* Show all markers, and center on the first */
        if (bounds.getNorthEast().lat() != bounds.getSouthWest().lat() ||
            bounds.getNorthEast().lng() != bounds.getSouthWest().lng())
          gMap.fitBounds(bounds);
        if (first)
          gMap.setCenter(first);
      });
    }
  };

  window.makeGeocodedInputWidget = function (options) {
    var inputElement = options.input;
    var iconElement = jQuery('<img id="geocoded_status" src="/static/spinner.gif"' +
                               ' alt="status" style="display:none">')[0];
    var messageElement = jQuery('<div id="geocoded_location">')[0];
    jQuery(inputElement).after(messageElement).after(iconElement);

    var statusIcons = {
      "spinner": "/static/spinner.gif",
      "ok":      "/static/accept.png",
      "error":   "/static/exclamation.png"
    };

    function updateGeocodeStatus(status, message) {
      iconElement.writeAttribute("src", statusIcons[status]);
      iconElement.show();

      if (message) {
        messageElement.update(message);
      }
    }

    function geocodeLocation() {
      var el = this;
      updateGeocodeStatus('spinner');

      /* Geocode the address with Google */
      var geocoder = new google.maps.Geocoder();
      var request = {
        address: el.getValue()
      };
      geocoder.geocode(request, function(results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
          var result = results.first();
          var location = result.geometry.location;
          updateGeocodeStatus('ok', result.formatted_address);
          jQuery(options.latitude).val(location.lat());
          jQuery(options.longitude).val(location.lng());
        } else {
          updateGeocodeStatus('error');
        }
      });
    }

    loadMaps(function() {
      inputElement.observe('change', geocodeLocation);
    });
  };
})(jQuery);
