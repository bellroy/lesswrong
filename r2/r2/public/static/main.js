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

$(document).ready(function() {

  /* Dropdowns in main menu */
  dropdownSel = 'ul#nav li img.dropdown';
  $(dropdownSel).click(function(e) {
    var ul = $(this).next('ul');
    var isVisible = $(ul).is(':visible');

    /* Hide all dropdowns */
    $(dropdownSel).next('ul').hide();

    /* If it wasn't visible initially, show it */
    if (!isVisible)
      ul.show();

    /* Register for any clicks to close the dropdown */
    $(document).one("click", function() {
      $(ul).hide();
    });

    return false;
  });

  // Post filter control
  $('#post-filter div.filter-active').click(function() {
    $(this).toggleClass('open');
    $(this).next('div.filter-options').toggle();
    return false;
  });

  // Comment filter control
  $('#comment-controls div.filter-active').click(function() {
    $(this).toggleClass('open');
    $(this).next('div.filter-options').toggle();
    return false;
  });

  // Button tooltips
  $('div.tools div.vote a, div.tools div.boxright a.edit, div.tools div.boxright a.save, div.boxright a.hide, div.comment-links ul li a').qtip({
    position: {
      my: 'bottom center',
      at: 'top center'
    },
    style: {
      classes: 'ui-tooltip-lesswrong',
      tip: {
	border: 0,
	corner: 'bottom center',
	height: 7, /* If you adjust this, you must change qtip-tip-ie.gif to the same size */
	width: 10 /* If you adjust this, you must change qtip-tip-ie.gif to the same size */
      }
    }
  });
});

})(jQuery);