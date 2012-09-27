function makeGeocodedInputWidget(options) {
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
}

(function() {
  document.observe("dom:loaded", function() {
    createMap( $('map') );
  });

  function setTimeZone(date) {
    $$('input[name="tzoffset"]').each(function(el) {
      var tz = (new Date()).getTimezoneOffset()
      el.setValue(tz / -60)
    });
  }

  document.observe("dom:loaded", function() {
    var form = $('newmeetup');
    if (form) {
      form.focusFirstElement();

      setTimeZone();

      makeGeocodedInputWidget({
        input:    $('location'),
        latitude: $$('input[name="latitude"]').first(),
        latitude: $$('input[name="longitude"]').first()
      });

      Protoplasm.use('timepicker', function() { /* Used by datepicker below */
        Protoplasm.use('datepicker', function() {
          var picker = new Control.DatePicker($$('input.date').first(), {epoch: true, timePicker: true});
        });
      });
    }
  });
})();
