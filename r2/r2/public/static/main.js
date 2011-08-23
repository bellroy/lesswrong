(function ($) {

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

  function isiPhone() {
    return ((navigator.platform.indexOf("iPhone") != -1) ||
            (navigator.platform.indexOf("iPod") != -1) ||
            (navigator.platform.indexOf("iPad") != -1));
  };

  /* Don't do qtip tooltips with iphones (and related), it seems to interfer with the 
     normal onclick behaviour */
  if (!isiPhone()) {
    // Button tooltips
    $('div.tools div.vote a, div.tools div.boxright a.edit, div.tools div.boxright a.save, \
       div.boxright a.hide, div.comment-links ul li a, \
       .userinfo .score, .userinfo .monthly-score').qtip({
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
  }
});

})(jQuery);