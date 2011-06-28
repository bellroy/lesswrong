(function ($) {
  /* Show Meetup map */
  window.createMap = function (map) {
    if (map) {
      loadMaps(function() { 
        var markers = $('.marker', map);
        var cntrData = markers.first();
        var lat = cntrData.attr('data-latitude');
        var lng = cntrData.attr('data-longitude');
        var cntr = new google.maps.LatLng(lat,lng);
        var myOptions = {
          zoom: 16,
          center: cntr,
          mapTypeId: google.maps.MapTypeId.ROADMAP
        };
        
        var gMap = new google.maps.Map(map, myOptions);

        markers.each(function(i,m) {
          var lat = m.readAttribute('data-latitude');
          var lng = m.readAttribute('data-longitude');
          latlng = new google.maps.LatLng(lat, lng);
          new google.maps.Marker({
            map: gMap,
            draggable: false,
            animation: google.maps.Animation.DROP,
            position: latlng,
            title: m.readAttribute('data-title')
          });
        });
      });
    }
  };
})(jQuery);
