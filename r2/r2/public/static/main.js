(function ($) {

$(document).ready(function() {

	// Dropdowns in main menu
	$('ul#nav li img.dropdown').click(function() {
		$(this).next('ul').toggle();
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