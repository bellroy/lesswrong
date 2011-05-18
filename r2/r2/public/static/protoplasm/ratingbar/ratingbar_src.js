if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize ratingbar');
if (window.Control == undefined) Control = {};

Protoplasm.loadStylesheet('rating.css', 'ratingbar');

/**
 * class Control.RatingBar
 * 
 * Create a click-a-star style rating bar.
**/
Control.RatingBar = Class.create({
	initialize: function (element, options) {

		this.element = $(element);
		this.stars = [];
		this.options = Object.extend({
				min: 1,
				max: 5,
				rating: 0,
				starClass: 'rating_star',
				onClass: 'rating_on',
				halfClass: 'rating_half',
				hoverClass: 'rating_hover',
				waitForUpdate: false,
				onclick: Prototype.K,
				onhover: Prototype.K
			}, options || {});
		this.rating = this.options.rating;
		this.loading = document.createElement('div');
		this.loading.className = 'rating_loading';
		this.animating = false;
		this.createRatingBar();
		this.element.onmouseout = function() {
			if (!this.animating) this.resetRating();
			}.bind(this)
	},
	createRatingBar: function() {

		this.element.cleanWhitespace();
		this.element.style.height = '20px';

		if (this.element.childNodes.length == 1
				&& this.element.firstChild.nodeType == 3) {
			this.rating = this.element.firstChild.nodeValue;
			this.element.removeChild(this.element.firstChild);
		}

		if (!this.element.childNodes.length) {
			// Not prepopulated, setup the star divs
			for (var i = this.options.min; i <= this.options.max; ++i) {
				var star = new Element('div');
				star.addClassName(this.options.starClass);
				this.element.appendChild(star);
			}	

		} else {
			// Guess current rating
			this.rating = this.options.min;
			for (var i = 1; i < this.element.childNodes.length; ++i) {
				var child = $(this.element.childNodes[i]); 
				if (child.hasClassName(this.options.onClass))
					this.rating++;
				else if (child.hasClassName(this.options.halfClass))
					this.rating += .5;
			}
		}

		for (var i = 0; i < this.element.childNodes.length; ++i) {
			var child = $(this.element.childNodes[i]); 
			if (child.hasClassName(this.options.starClass)) {
				this.setStarBehavior(child, i + this.options.min)
				this.stars.push(child);
			}
		}

		if (this.options.rating)
			this.rating = this.options.rating;

		if (this.rating)
			this.showRating(this.rating);

	},
	setStarBehavior: function(star, rating) {
		star.onmouseover = this.hoverRating.bind(this, rating);
		star.onclick = this.doRating.bind(this, rating);
	},
	hoverRating: function(rating) {
		rating = Math.ceil(rating);
		for (var i = 0; i < this.stars.length; ++i) {
			this.stars[i].className = this.options.starClass;
			var current = i + this.options.min;
			if (current <= rating)
				this.stars[i].addClassName(this.options.hoverClass);
		}
		if (this.options.onhover)
			this.options.onhover(this);
	},
	doRating:  function(rating) {
		this.rating = rating;
		this.animateBar(rating, 1, 150, this.resetRating.bind(this));
		if (this.options.onclick)
			this.options.onclick(this);
	},
	animateBar: function(rating, times, delay, complete, iteration, dohover) {
		this.animating = true;
		if (!iteration) iteration = 0;
		if (iteration < times) {
			if (dohover) {
				this.hoverRating(rating);
				iteration++;
			} else {
				this.showRating(rating);
			}
			setTimeout(this.animateBar.bind(this, rating, times, delay, complete, iteration, !dohover), delay);
		} else if (iteration >= times) {
			setTimeout(function() { this.animating = false; complete(); }.bind(this), 500);
		}
	},
	showRating: function(rating) {
		for (var i = 0; i < this.stars.length; ++i) {
			this.stars[i].className = this.options.starClass;
			var current = i + this.options.min;
			if (current <= rating)
				this.stars[i].addClassName(this.options.onClass);
			else if (current - 0.5 <= rating)
				this.stars[i].addClassName(this.options.halfClass);
		}
	},
	resetRating: function() {
		if (!this.animating) {
			this.showRating(this.rating);
			if (this.options.input)
				$(this.options.input).value = this.rating;
		}
	},
	setLoading: function(loading) {
		if (loading) {
			if (!this.loading.parentNode)
				this.element.appendChild(this.loading);
		} else {
			$(this.loading).remove();
		}
	}
});

Protoplasm.register('ratingbar', Control.RatingBar);
