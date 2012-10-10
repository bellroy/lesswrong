(function ($) {
  /* Show Meetup map */
  window.createMap = function (map) {
    if (!map)
      return;

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
        var latlng = new google.maps.LatLng(lat, lng);
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
      if (bounds.getNorthEast().lat() !== bounds.getSouthWest().lat() ||
          bounds.getNorthEast().lng() !== bounds.getSouthWest().lng())
        gMap.fitBounds(bounds);
      if (first)
        gMap.setCenter(first);
    });
  };

  window.makeGeocodedInputWidget = function (options) {
    var prompt = options.prompt || "";
    var inputElement = options.input;
    var iconElement = $('<img class="field-status-icon" src="about:blank"' +
                               ' alt="" style="display:none">')[0];
    var messageElement = $('<div class="form-info-line" />').text(prompt)[0];
    $(inputElement).after(messageElement).after(iconElement);

    var cancelSubmit = false;
    var onComplete = null;

    var statusIcons = {
      "none":    {show: false, blank: true,  src: "about:blank"},
      "spinner": {show: true,  blank: true,  src: "/static/spinner.gif"},
      "ok":      {show: true,  blank: false, src: "/static/accept.png"},
      "error":   {show: true,  blank: true,  src: "/static/exclamation.png"}
    };

    function updateGeocodeStatus(status, message) {
      var st = statusIcons[status];
      $(iconElement)
        .attr({src: st.src})
        .css({display: st.show ? "" : "none"});

      if (st.blank) {
        $([options.latitude, options.longitude]).val('');
      }
      if (message !== void 0) {
        $(messageElement).text(message);
      }
    }

    function geocodeLocation() {
      var addr = this.value;

      if (!addr) {
        updateGeocodeStatus("none", prompt);
        return;
      }

      /* Geocode the address with Google */
      updateGeocodeStatus("spinner");
      var geocoder = new google.maps.Geocoder();
      var request = {address: addr};
      cancelSubmit = true;
      geocoder.geocode(request, function(results, status) {
        if (status === google.maps.GeocoderStatus.OK) {
          var result = results.first();
          var location = result.geometry.location;
          updateGeocodeStatus("ok", result.formatted_address);
          $(options.latitude).val(location.lat());
          $(options.longitude).val(location.lng());
        } else {
          updateGeocodeStatus("error", prompt);
        }

        cancelSubmit = false;
        if (onComplete)
          onComplete();
      });
    }

    loadMaps(function() {
      $(inputElement).bind("change", geocodeLocation).trigger("change");

      // If the form is submitted while we're waiting for geocoded
      // coordinates, defer the submission until afterwards.
      var form = $(inputElement).closest("form");
      form.bind("submit", function (event) {
        inputElement.blur();
        if (cancelSubmit) {
          event.preventDefault();
          onComplete = function () {
            form.submit();
          };
        }
      });
    });
  };
})(jQuery);
