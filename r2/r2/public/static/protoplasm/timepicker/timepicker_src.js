if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize timepicker');
if (typeof Control == 'undefined') Control = {};

Protoplasm.loadStylesheet('timepicker.css', 'timepicker');

/**
 * class Control.TimePicker
 * 
 * Transforms an ordinary input textbox into a time picker.
 *
 * Control ID: `timepicker`
 *
 * Features:
 *
 * * Allows user to specify a time format
 *
 * Example: <a href="http://jongsma.org/software/protoplasm/control/timepicker">Time
 * Picker demo</a>
**/
Control.TimePicker = Class.create({

/**
 * new Control.TimePicker(element[, options])
 * - element (String | Element): A `<input type="text">` element (or DOM ID).
 * - options (Hash): Additional options for the control.
 *
 * Create a new time picker from the given `<input type="text">`
 * element.
 *
 * Additional options:
 *
 * * icon: The URL of the icon to display on the control
 * * format: The time format (default 'HH:mm:ss')
 * * use24hrs: Show 24 hours in the time picker instead of
 *   AM/PM (default false)
 * * onChange: Callback function when the time is changed.
 *   A Date object is passed as the parameter.
 * * onSelect: Callback function when the time is selected.
 *   A Date object is passed as the parameter.
**/
	initialize: function (element, options) {

		element = $(element);

		if (tp = element.retrieve('timepicker'))
			tp.destroy();

		// Wrap to avoid positioning errors from padding/margins
		var wrapper = element.wrap('span', {'style': 'position:relative;'});

		options = Object.extend({
			format: 'HH:mm:ss'
			}, options || {});

		if (!options.icon)
			options.icon = Protoplasm.base('timepicker')+'clock.png';

/**
 * Control.TimePicker#element -> Element
 *
 * The underlying `<input>` element passed to the constructor.
**/
		this.element = element;
		this.label = element;
		this.wrapper = wrapper;
		this.options = options;
		this.changeHandler = options.onChange;
		this.selectHandler = options.onSelect;
		options.onSelect = this.onSelect.bind(this);
		options.onChange = this.onChange.bind(this);
/**
 * Control.TimePicker#panel -> Control.TimePicker.Panel
 *
 * The panel dialog box linked to this control.  This may be
 * null if the control is not open.
**/
		// Lazy load to avoid excessive CPU usage with lots of controls on one page
		this.panel = null;
		this.dialog = null;

		this.listeners = [
			element.on('click', this.toggle.bindAsEventListener(this)),
			element.on('keydown', this.keyHandler.bindAsEventListener(this)),
			Event.on(window, 'unload', this.destroy.bind(this))
		];

		if (options.icon) {
			element.style.background = 'url('+options.icon+') right center no-repeat #FFF';
			this.oldPadding = element.style.paddingRight;
			element.style.paddingRight = '20px';
		}

		this.hideListener = null;
		this.keyListener = null;
		this.active = false;

		this.element.store('timepicker', this);

		// Extend element with public API
		this.element = Protoplasm.extend(element, {
			show: wrapper.show.bind(wrapper),
			hide: wrapper.hide.bind(wrapper),
			open: this.open.bind(this),
			toggle: this.toggle.bind(this),
			close: this.close.bind(this),
			destroy: this.destroy.bind(this)
		});

	},

/**
 * Control.TimePicker#destroy() -> null
 *
 * Destroy this control and return the underlying element to
 * its original behavior.
**/
	destroy: function() {
		Protoplasm.revert(this.element);
		this.listeners.invoke('stop');
		if (this.hideListener)
			this.hideListener.stop();
		if (this.keyListener)
			this.keyListener.stop();
		this.wrapper.parentNode.replaceChild(this.element, this.wrapper);
		this.element.style.paddingRight = this.oldPadding;
		this.element.store('timepicker', null);
	},

	clickHandler: function(e) {
		var element = Event.element(e);
		do {
			if (element == this.element || element == this.label
					|| element == this.dialog)
				return;
		} while (element = element.parentNode);
		this.close();
	},

	setValue: function(time) {
		var h = time.getHours();
		var m = time.getMinutes();
		var s = time.getSeconds();
		var a = '';
		if (!this.options.use24hrs) {
			a = ' AM';
			if (h == 0) {
				h = 12;
			} else if (h > 11) {
				if (h > 12)
					h -= 12;
				a = ' PM';
			}
		}
		h = h < 10 ? '0'+h : h;
		m = m < 10 ? '0'+m : m;
		s = s < 10 ? '0'+s : s;
		this.element.value = h+':'+m+':'+s+a;
	},

	onSelect: function(time) {
		this.setValue(time);
		this.close();
		if (this.selectHandler)
			this.selectHandler(time);
	},

	onChange: function(time) {
		this.setValue(time);
		if (this.changeHandler)
			this.changeHandler(time);
	},

/**
 * Control.TimePicker#toggle() -> null
 *
 * Toggle the visibility of the picker panel for this control.
**/
	toggle: function(e) {
		if (this.active)
			this.close();
		else
			setTimeout(this.open.bind(this));
	},

	keyHandler: function(e) {
		switch (e.keyCode) {
			case Event.KEY_ESC:
				this.close();
				return;
			case Event.KEY_RETURN:
				this.close();
				return;
			case Event.KEY_TAB:
				this.close();
				return;
			case Event.KEY_DOWN:	
				if (!this.dialog || !this.dialog.parentNode) {
					this.open();
					Event.stop(e);
				}
		}
		if (this.pickerActive)
			return false;
	},

	docKeyHandler: function(e) {
		switch (e.keyCode) {
			case Event.KEY_ESC:
				this.close();
				return;
			case Event.KEY_RETURN:
				this.close();
				Event.stop(e);
				return;
		}
		if (this.pickerActive)
			return false;
	},

/**
 * Control.DatePicker#open() -> null
 *
 * Show the picker panel for this control.
**/
	open: function () {
		if (!this.active) {
			if (!this.dialog) {
				this.panel = new Control.TimePicker.Panel(this.options);
				this.dialog = new Element('div', { 'class': '_pp_frame_small',
					'style': 'position:absolute;' });
				this.dialog.insert(this.panel.element);
			}

			var layout = this.label.getLayout();
			var offsetTop = layout.get('border-box-height') - layout.get('border-bottom');
			document.body.appendChild(this.dialog);
			this.dialog.clonePosition(this.label, {
				'setWidth': false,
				'setHeight': false,
				'offsetTop': offsetTop,
				'offsetLeft': -3
				});
			this.dialog.style.zIndex = '99';
			this.panel.setTime(this.parse(this.element.value));
			this.panel.hours.focus();
			this.hideListener = document.on('click', this.clickHandler.bindAsEventListener(this));
			this.keyListener = document.on('keydown', this.docKeyHandler.bindAsEventListener(this));
			this.active = true;
		}
	},

	parse: function(str) {
		var p, h, m, s, ap;
		if (!this.options.use24hrs) {
			p = str.split(/ /);
			if (p.length > 1)
				ap = p[1].toUpperCase();
			str = p[0];
		}
		p = str.split(':');
		h = p[0] || 0;
		m = p[1] || 0;
		s = p.length > 2 ? p[2] : 0;
		if (!this.options.use24hrs) {
			if (ap == 'AM' && h == 12)
				h = 0;
			else if (h < 12 && ap == 'PM')
				h += 12;
		}
		d = new Date();
		d.setHours(h);
		d.setMinutes(m);
		d.setSeconds(s);
		return d;
	},

/**
 * Control.TimePicker#close() -> null
 *
 * Hide the picker panel for this control.
**/
	close: function() {
		if(this.active) {
			this.dialog.remove();
			this.active = false;
			if (this.hideListener)
				this.hideListener.stop();
			if (this.keyListener)
				this.keyListener.stop();
		}
	}

});

/**
 * class Control.TimePicker.Panel
 *
 * The dialog panel that is displayed when the time picker is opened.
**/
Control.TimePicker.Panel = Class.create({

/**
 * new Control.TimePicker.Panel([options])
 * - options (Hash): Additional options for the panel.
 *
 * Create a new time picker panel.
 *
 * Additional options:
 *
 * * use24hrs: Show 24 hours in the time picker instead of
 *   AM/PM (default false)
 * * onChange: Callback function when the time is changed.
 *   A Date object is passed as the parameter.
 * * onSelect: Callback function when the time is selected.
 *   A Date object is passed as the parameter.
**/
	initialize: function(options) {

		this.options = Object.extend({
			}, options || {});

		this.time = this.options.time || new Date();
		this.ampm = 'AM';
		this.element = this.createPicker();

		this.element.on('selectstart', function(e) {
			Event.stop(e); }.bindAsEventListener(this));
	},

	createPicker: function() {

		var picker = new Element('div', {'class': '_pp_timepicker '+this.options.className});

		this.hours = new Element('input', {'type': 'text', 'class': '_pp_timepicker_input', 'value': '00'});
		this.minutes = new Element('input', {'type': 'text', 'class': '_pp_timepicker_input', 'value': '00'});
		this.seconds = new Element('input', {'type': 'text', 'class': '_pp_timepicker_input', 'value': '00'});

		var table = new Element('table', {'cellPadding': 0, 'cellSpacing': 0, 'border': 0});
		var row = table.insertRow(0);

		row.appendChild(this.createCell(this.hours, this.options.use24hrs ? 23 : 12,
			this.options.use24hrs ? 0 : 1));
		row.appendChild(new Element('td').update(':'));
		row.appendChild(this.createCell(this.minutes, 59, 0));
		row.appendChild(new Element('td').update(':'));
		row.appendChild(this.createCell(this.seconds, 59, 0));

		if (!this.options.use24hrs) {
			var td = new Element('td');
			this.am = new Element('div', {'class': '_pp_timepicker_ampm _pp_highlight'}).update('AM');
			this.am.on('click', function() {
				this.ampm = 'AM';
				this.pm.removeClassName('_pp_highlight');
				this.am.addClassName('_pp_highlight');
				this.onChange();
				}.bindAsEventListener(this));
			this.pm = new Element('div', {'class': '_pp_timepicker_ampm'}).update('PM');
			this.pm.on('click', function() {
				this.ampm = 'PM';
				this.am.removeClassName('_pp_highlight');
				this.pm.addClassName('_pp_highlight');
				this.onChange();
				}.bindAsEventListener(this));
			td.appendChild(this.am);
			td.appendChild(this.pm);
			row.appendChild(td);
		}

		picker.appendChild(table);

		return picker;

	},

	createCell: function(input, maxValue, minValue) {

		var td = new Element('td');

		input.on('keydown', function(e) {
			if (e.keyCode == Event.KEY_UP) {
				this.increment(input, maxValue, minValue);
				this.onChange();
				Event.stop(e);
			} else if (e.keyCode == Event.KEY_DOWN) {
				this.decrement(input, maxValue, minValue);
				this.onChange();
				Event.stop(e);
			} else if (e.keyCode == Event.KEY_RETURN) {
				this.onSelect();
				Event.stop(e);
				return false;
			}}.bindAsEventListener(this));
		input.on('change', function(e) {
			var current = input.value*1;
			input.value = current < 10 ? '0'+current : current;
			this.onChange();
			}.bindAsEventListener(this));
		input.on('focus', function(e) {
			input.select();
			}.bindAsEventListener(this));

		var up = new Element('div', {'class': '_pp_highlight _pp_timepicker_up'});
		this.setBehavior(up, input, this.increment, maxValue, minValue);

		var down = new Element('div', {'class': '_pp_highlight _pp_timepicker_down'});
		this.setBehavior(down, input, this.decrement, maxValue, minValue);

		td.appendChild(up);
		td.appendChild(input);
		td.appendChild(down);

		return td;

	},

	setBehavior: function(button, input, action, maxValue, minValue) {
		var pressed = false;
		var multiple = (maxValue - minValue > 30) ? 5 : 1;
		button.on('mousedown', function(e) {
				pressed = true;
				var repeater;
				setTimeout(function() {
					if (pressed)
						repeater = setInterval(function() {
							if (pressed) {
								action(input, maxValue, minValue, multiple);
								this.onChange();
							} else
								clearInterval(repeater);
						}.bind(this), 200);
				}.bind(this), 500);
				action(input, maxValue, minValue);
				this.onChange();
			}.bindAsEventListener(this));
		button.on('mouseup', function(e) {
			pressed = false;
			}.bindAsEventListener(this));
		button.on('mouseout', function(e) {
			pressed = false;
			}.bindAsEventListener(this));
	},

	increment: function(input, maxValue, minValue, multiple) {
		if (!multiple) multiple = 1;
		var current = input.value*1;
		current += multiple;
		current = current - current % multiple;
		if (current > maxValue)
			current = minValue;
		input.value = current < 10 ? '0'+current : current;
	},

	decrement: function(input, maxValue, minValue, multiple) {
		if (!multiple) multiple = 1;
		var current = input.value*1;
		current -= multiple;
		current = current - current % multiple;
		if (current < minValue)
			current = maxValue;
		input.value = current < 10 ? '0'+current : current;
	},

	onChange: function() {
		if (this.options.onChange)
			this.options.onChange(this.getTime());
	},

	onSelect: function() {
		if (this.options.onSelect)
			this.options.onSelect(this.getTime());
	},

	getTime: function() {
		var d = new Date();
		var h = this.hours.value * 1;
		if (!this.options.use24hrs) {
			if (h == 12 && this.ampm == 'AM')
				h = 0;
			else if (h < 12 && this.ampm == 'PM')
				h += 12;
		}
		d.setHours(h);
		d.setMinutes(this.minutes.value*1);
		d.setSeconds(this.seconds.value*1);
		return d;
	},

	setTime: function(time) {
		var h = time.getHours();
		var m = time.getMinutes();
		var s = time.getSeconds();
		if (!this.options.use24hrs) {
			this.ampm = 'AM';
			this.am.addClassName('_pp_highlight');
			this.pm.removeClassName('_pp_highlight');
			if (h > 12) {
				h -= 12;
				this.ampm = 'PM';
				this.pm.addClassName('_pp_highlight');
				this.am.removeClassName('_pp_highlight');
			} else if (h == 0) {
				h = 12;
			}
		}
		this.hours.value = h >= 10 ? h : '0'+h;
		this.minutes.value = m >= 10 ? m : '0'+m;
		this.seconds.value = s >= 10 ? s : '0'+s;
	}

});

Protoplasm.register('timepicker', Control.TimePicker);
