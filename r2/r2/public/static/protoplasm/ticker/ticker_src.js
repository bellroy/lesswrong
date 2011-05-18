if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize ticker');
if (typeof Control == 'undefined') Control = {};

/**
 * class Control.Ticker
 * 
 * Creates a scrolling ticker (for stock quotes, etc) out of a series
 * of elements.
**/
Control.Ticker = Class.create({

	initialize: function(element, options) {

		options = Object.extend({
			'generator': null,
			'interval': 10,
			'step': -1,
			'gap': 50
			}, options || {});

		element.style.overflow = 'hidden';
		element.style.position = 'relative';
		element.on('mouseover', function(e) {
			this.setScrollDelay(options.interval * 2);
		}.bindAsEventListener(this));
		element.on('mouseout', function(e) {
			this.setScrollDelay(options.interval);
		}.bindAsEventListener(this));
		scroller = new Element('div', {
			'style': 'position:absolute;white-space:nowrap;'});

		content = new Element('div');
		while (element.firstChild)
			content.appendChild(element.firstChild);

		element.appendChild(scroller);

		this.element = $(element);
		this.options = options;
		this.scroller = scroller;
		this.interval = options.interval;

		this.offset = 0;
		this.reset = 0;
		this.max = 0;

		this.update(options.generator || function() {
				return content.childNodes
			});
		// Start at right end of ticker
		this.offset = this.element.offsetWidth;
		this.start();
	},

	setScrollDelay: function(delay) {
		this.interval = delay;
		if (this.timer) {
			this.stop();
			this.start();
		}
	},

	start: function() {
		this.timer = setInterval(function() {
				this.scroll(this.options.step);
			}.bind(this), this.interval);
	},

	scroll: function(pixels) {
		this.offset = this.offset + pixels;
		if (this.offset < -this.max)
			this.offset = this.reset;
		this.scroller.style.left = this.offset + 'px';
	},

	refresh: function() {
		if (this.options.generator)
			this.update(this.options.generator);
	},

	update: function(generator) {
		while (this.scroller.firstChild)
			this.scroller.removeChild(this.scroller.firstChild);

		this.scroller.appendChild(this.box(generator()));
		var width = this.scroller.offsetWidth;

		this.max = width;
		this.reset = 0;

		this.scroller.appendChild(this.box(generator()));
		if (this.scroller.offsetWidth == width) {
			this.reset = this.element.offsetWidth;
		} else {
			while (this.scroller.offsetWidth < this.element.offsetWidth + width)
				this.scroller.appendChild(this.box(generator()));
		}

	},

	box: function(nodes) {
		var wrapper = new Element('div', {'style':
			'position:relative;display:inline-block;margin-right:'
			+ this.options.gap + 'px;'});
		if (Object.isArray(nodes))
			$A(nodes).each(function(n) { wrapper.appendChild(n); });
		else
			wrapper.appendChild(nodes);
		return wrapper;
	},

	stop: function() {
		if (this.timer) {
			clearInterval(this.timer);
			this.timer = null;
		}
	}

});

Protoplasm.register('ticker', Control.Ticker);
