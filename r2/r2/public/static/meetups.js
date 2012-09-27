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
