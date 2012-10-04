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
    var prompt = options.prompt || "";
    var inputElement = options.input;
    var iconElement = jQuery('<img class="field-status-icon" src="about:blank"' +
                               ' alt="" style="display:none">')[0];
    var messageElement = jQuery('<div class="form-info-line" />').text(prompt)[0];
    jQuery(inputElement).after(messageElement).after(iconElement);

    var statusIcons = {
      "none":    {show: false, blank: true,  src: "about:blank"},
      "spinner": {show: true,  blank: true,  src: "/static/spinner.gif"},
      "ok":      {show: true,  blank: false, src: "/static/accept.png"},
      "error":   {show: true,  blank: true,  src: "/static/exclamation.png"}
    };

    function updateGeocodeStatus(status, message) {
      var st = statusIcons[status];
      iconElement.writeAttribute("src", st.src);
      iconElement[st.show ? "show" : "hide"]();

      if (st.blank) {
        jQuery([options.latitude, options.longitude]).val('');
      }
      if (message !== void 0) {
        messageElement.update(message);
      }
    }

    function geocodeLocation() {
      var addr = this.getValue();

      if (!addr) {
        updateGeocodeStatus("none", prompt);
        return;
      }

      /* Geocode the address with Google */
      updateGeocodeStatus("spinner");
      var geocoder = new google.maps.Geocoder();
      var request = {address: addr};
      geocoder.geocode(request, function(results, status) {
        if (status !== google.maps.GeocoderStatus.OK) {
        updateGeocodeStatus("error", prompt);
          return;
        }

        var result = results.first();
        var location = result.geometry.location;
        updateGeocodeStatus("ok", result.formatted_address);
        jQuery(options.latitude).val(location.lat());
        jQuery(options.longitude).val(location.lng());
      });
    }

    loadMaps(function() {
      inputElement.observe('change', geocodeLocation);
      geocodeLocation.call(inputElement);
    });
  };
})(jQuery);
