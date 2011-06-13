(function ($) {

$(document).ready(function() {

	$('ul li:first-child').addClass('first-child');
	$('ul li:last-child').addClass('last-child');
	$('#side-comments div.inline-comment:last-child, #side-posts div.reddit-link:last-child, #side-contributors div.contributors div.user:last-child').addClass('last-child');

});

})(jQuery);