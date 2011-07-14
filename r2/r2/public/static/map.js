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
})(jQuery);
