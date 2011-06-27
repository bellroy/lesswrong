(function() {

  document.observe("dom:loaded", function() {
    createMap( $('map') );
  });

  /* Add Meetup */
  function setTimeZone(date) {
    $$('input[name="tzoffset"]').each(function(el) {
      var tz = (new Date()).getTimezoneOffset()
      el.setValue(tz / -60)
    });
  }

  var statusIcons = {
    "spinner": "/static/spinner.gif",
    "ok": "/static/accept.png",
    "error": "/static/exclamation.png"
  };

  function updateGeocodeStatus(status, message) {
    var el = $('geocode_status');
    el.writeAttribute('src', statusIcons[status]);
    el.show();

    if (message) {
      $('geocoded_location').update(message);
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
        $$('input[name="latitude"]').first().setValue(location.lat());
        $$('input[name="longitude"]').first().setValue(location.lng());
      }
      else {
        updateGeocodeStatus('error');
      }
    });
  }

  document.observe("dom:loaded", function() {
    var form = $('newmeetup');
    if (form) {
      form.focusFirstElement();

      loadMaps(function() {
        $('location').observe('change', geocodeLocation);
      });

      /* Fill in the current time zone */
      setTimeZone();

      Protoplasm.use('timepicker', function() { /* Used by datepicker below */
        Protoplasm.use('datepicker', function() {
          var picker = new Control.DatePicker($$('input.date').first(), {epoch: true, timePicker: true});
        });
      });
    }
  });
})();
