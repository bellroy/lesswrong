if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize datepicker');
if (typeof Control == 'undefined') Control = {};

Protoplasm.use('timepicker');
Protoplasm.loadStylesheet('datepicker.css', 'datepicker');

/**
 * class Control.DatePicker
 * 
 * Transforms an ordinary input textbox into an interactive date picker.
 * When the textbox is clicked (or the down arrow is pressed), a calendar
 * appears that the user can browse through and select a date.
 *
 * Control ID: `datepicker`
 *
 * Features:
 *
 * * Allows user to specify a date format
 * * Easy to localize
 *
 * Example: <a href="http://jongsma.org/software/protoplasm/control/datepicker">Date
 * Picker demo</a>
**/
Control.DatePicker = Class.create({

/**
 * new Control.DatePicker(element[, options])
 * - element (String | Element): A `<input type="text">` element (or DOM ID).
 * - options (Hash): Additional options for the control.
 *
 * Create a new date picker from the given `<input type="text">`
 * element.
 *
 * Additional options:
 *
 * * icon: The URL of the icon to display on the control
 * * monthCount: The number of calendar months to display at one time
 * * layout: Layout mode for multiple calendars: 'horizontal' (default) or 'vertical'
 * * range: Use date range selection instead of a single date.
 *   Requires multiple `<input>` elements (see rangeEnd below).
 * * rangeEnd: The element for storing a date range's end date in. If a rangeEnd
 *   element is not specified, it will automatically look for one as a next
 *   sibling of `element`.
 * * minDate: The minimum date that is allowed to be selected
 * * maxDate: The maximum date that is allowed to be selected
 * * locale: Set the internationalization locale code
 * * manual: Allow manual date entry by typing (default true)
 * * epoch: The date posted to the server will be as a unix
 *   timestamp representing the milliseconds since 1-1-1970
 * * timePicker: Display a time picker (default false)
 * * use24hrs: Show 24 hours in the time picker instead of
 *   AM/PM (default false)
 * * onSelect: Callback function when a date/time is selected.
 *   A Date object is passed as the parameter.
 * * onHover: Callback function when the active date changes
 *   via keyboard navigation.  A Date object is passed as
 *   the parameter.
**/
	initialize: function(element, options) {
		
		element = $(element);

		if (dp = element.retrieve('datepicker'))
			dp.destroy();

		// Wrap to avoid positioning errors from padding/margins
		var wrapper = element.wrap(new Element('span'));
		wrapper.style.position = 'relative';

		options = Object.extend({
						timePicker: false,
						manual: true
					}, options || {});

		if (!options.icon)
			options.icon = Protoplasm.base('datepicker')+'calendar.png';

/**
 * Control.DatePicker#element -> Element
 *
 * The underlying `<input>` element passed to the constructor.
**/
		this.element = element;
		this.anchor = element;
		this.wrapper = wrapper;
/**
 * Control.DatePicker#panel -> Control.DatePicker.Panel
 *
 * The panel dialog box linked to this control.  This may be
 * null if the control is not open.
**/
		// Lazy load to avoid excessive CPU usage with lots of controls on one page
		this.panel = null;
		this.dialog = null;

		this.handlers = { onClick: options.onClick,
				onHover: options.onHover,
				onSelect: options.onSelect };

		this.options = Object.extend(options || {}, {
				onClick: this.pickerClicked.bind(this),
				onHover: this.dateHover.bind(this),
				onSelect: this.datePicked.bind(this)
			});

		var locale = options && options.locale ? options.locale : 'en_US';
		try {
			this.setLocale(new Control.DatePicker.i18n(locale));
		} catch(e) {
			// Load available locale on demand
			// TODO: fallback to Protoplasm.require() if URL is from different domain
			new Ajax.Request(Protoplasm.base('datepicker')+'locales/'+locale+'.js', {
				onSuccess: function(transport) {
					eval(transport.responseText);
					this.setLocale(new Control.DatePicker.i18n(locale), true);
				}.bind(this),
				onFailure: function(transport) {
					this.setLocale(new Control.DatePicker.i18n('en_US'), true);
				}.bind(this)
			});
		}

		this.listeners = [
			document.on('keydown', this.docKeyHandler.bindAsEventListener(this)),
			Event.on(window, 'unload', this.destroy.bind(this))
		];

		this.originalRange = { start: null, end: null };
		if (options.range)
			this.rangeEnd = options.rangeEnd ? $(options.rangeEnd) : wrapper.next('input[type=text]');

		if (options.icon) {
			element.style.background = 'url('+options.icon+') right center no-repeat #FFF';
			// Prevent text writing over icon
			this.oldPadding = element.style.paddingRight;
			element.style.paddingRight = '20px';
			if (this.rangeEnd) {
				this.rangeEnd.style.background = 'url('+options.icon+') right center no-repeat #FFF';
				this.rangeEnd.style.paddingRight = '20px';
			}
		}

		if (options.epoch) {
			this.startLabel = this.makeEpochLabel(element);
			this.addListener(this.startLabel);
			this.anchor = this.startLabel;
			if (this.rangeEnd) {
				this.endLabel = this.makeEpochLabel(this.rangeEnd);
				this.addListener(this.endLabel);
			}
		} else {
			this.addListener(element);
			if (this.rangeEnd)
				this.addListener(this.rangeEnd);
			element.readOnly = !this.options.manual;
		}

		this.hidePickerListener = null;

		this.pickerActive = false;
		this.element.store('datepicker', this);

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

	// Submit dates in milliseconds since 1/1/1970 00:00:00
	makeEpochLabel: function(e) {
		var r = e.clone();
		r.name = null;
		r.on('change', function() {
			var d = Control.DatePicker.DateFormat.parseFormat(
				r.value, this.options.currentFormat);
			if (d) e.value = d.getTime();
		});
		r.id = null;
		r.readOnly = !this.options.manual;
		e.type = 'hidden';
		if (e.value)
			r.value = this.options.currentFormat
				? Control.DatePicker.DateFormat.format(
					new Date(parseInt(e.value)), this.options.currentFormat)
				: '';
		e.insert({ after: r});
		return r;
	},

	addListener: function(elt) {
		this.listeners.push(elt.on('click', this.toggle.bindAsEventListener(this)));
		this.listeners.push(elt.on('keydown', this.keyHandler.bindAsEventListener(this)));
	},

	setLocale: function(locale, reset) {
		this.i18n = locale;
		this.options = this.i18n.inheritOptions(this.options);
		if (!this.options.range && this.options.timePicker)
			this.options.currentFormat = this.options.dateTimeFormat;
		else
			this.options.currentFormat = this.options.dateFormat;
		this.options.date = Control.DatePicker.DateFormat.parseFormat(this.element.value, this.options.currentFormat);
		if (this.options.range && this.rangeEnd)
			this.options.endDate = Control.DatePicker.DateFormat.parseFormat(this.rangeEnd.value, this.options.currentFormat);
		// Reset field labels
		if (reset) {
			var original = this.getValue();
			this.setValue(original.start, original.end);
		}
	},

/**
 * Control.DatePicker#destroy() -> null
 *
 * Destroy this control and return the underlying element to
 * its original behavior.
**/
	destroy: function() {
		Protoplasm.revert(this.element);
		this.listeners.invoke('stop');
		if (this.hidePickerListener)
			this.hidePickerListener.stop();
		this.wrapper.parentNode.replaceChild(this.element, this.wrapper);
		this.element.style.paddingRight = this.oldPadding;
		this.element.store('datepicker', null);
	},

	tr: function(str) {
		return this.i18n.tr(str);
	},
	clickHandler: function(e) {
		var element = Event.element(e);
		do {
			if (element == document)
				break;
			if (element == this.element
					|| element == this.startValue
					|| element == this.endValue
					|| element == this.dialog)
				return;
		} while (element = element.parentNode);
		// Next/Back buttons remove themselves from the layout before
		// we can check the event source
		if (!element)
			return;
		this.close();
	},
	pickerClicked: function() {
		if (this.handlers.onClick)
			this.handlers.onClick();
	},
	datePicked: function(start, end) {
		this.setValue(start, end);
		this.element.focus();
		this.close();
		if (this.handlers.onSelect)
			this.handlers.onSelect(start, end);
		if (this.element.onchange)
			this.element.onchange();
	},
	dateHover: function(start, end) {
		if (this.pickerActive) {
			this.setValue(start, end);
			if (this.handlers.onHover)
				this.handlers.onHover(start, end);
		}
	},
/**
 * Control.DatePicker#toggle() -> null
 *
 * Toggle the visibility of the picker panel for this control.
**/
	toggle: function(e) {
		if (this.pickerActive) {
			this.setValue(this.originalRange.start, this.originalRange.end);
			this.close();
		} else {
			setTimeout(this.open.bind(this));
		}
		//Event.stop(e);
		return false;
	},
	setValue: function(start, end) {
		startLabel = start ?  Control.DatePicker.DateFormat.format(start, this.options.currentFormat) : null;
		startValue = start && this.options.epoch ? start.getTime() : startLabel;
		endLabel = end ?  Control.DatePicker.DateFormat.format(end, this.options.currentFormat) : null;
		endValue = end && this.options.epoch ? end.getTime() : endLabel;

		this.element.value = startValue ? startValue : '';
		if (this.options.epoch)
			this.startLabel.value = startLabel ? startLabel : '';
		if (this.rangeEnd) {
			this.rangeEnd.value = endValue ? endValue : '';
			if (this.options.epoch)
				this.endLabel.value = endLabel ? endLabel : '';
		}
	},
	getValue: function() {
		var range = { start: null, end: null };
		if (this.element.value)
			range.start = this.options.epoch
				? new Date(parseInt(this.element.value))
				: Control.DatePicker.DateFormat.parseFormat(this.element.value, this.options.currentFormat);
		if (this.rangeEnd && this.rangeEnd.value)
			range.end = this.options.epoch
				? new Date(parseInt(this.rangeEnd.value))
				: Control.DatePicker.DateFormat.parseFormat(this.rangeEnd.value, this.options.currentFormat);
		return range;
	},
	docKeyHandler: function(e) {
		if (e.keyCode == Event.KEY_ESC)
			if (this.pickerActive) {
				this.setValue(this.originalRange.start, this.originalRange.end);
				this.close();
			}

	},
	keyHandler: function(e) {
		switch (e.keyCode) {
			case Event.KEY_ESC:
				if (this.pickerActive)
					this.setValue(this.originalRange.start, this.originalRange.end);
			case Event.KEY_TAB:
				this.close();
				return;
			case Event.KEY_DOWN:	
				if (!this.pickerActive) {
					this.open();
					Event.stop(e);
				}
		}
		if (this.pickerActive)
			return false;
	},
/**
 * Control.DatePicker#close() -> null
 *
 * Hide the picker panel for this control.
**/
	close: function() {
		if(this.pickerActive && !this.element.disabled) {
			this.panel.releaseKeys();
			this.dialog.remove();
			if (this.hidePickerListener) {
				this.hidePickerListener.stop();
				this.hidePickerListener = null;
			}
			this.pickerActive = false;
			Control.DatePicker.activePicker = null;
		}
	},
/**
 * Control.DatePicker#open() -> null
 *
 * Show the picker panel for this control.
**/
	open: function () {
		if (!this.pickerActive) {
			if (Control.DatePicker.activePicker)
				Control.DatePicker.activePicker.close();
			this.anchor.focus();
			if (!this.dialog) {
				this.panel = new Control.DatePicker.Panel(this.options);
				this.dialog = new Element('div', { 'class': '_pp_frame_small _pp_datepicker '
					+ this.options.className, 'style': 'position:absolute;' });
				this.dialog.appendChild(this.panel.element);
			}
			this.originalRange = this.getValue();

			var layout = this.anchor.getLayout();
			var offsetTop = layout.get('border-box-height') - layout.get('border-bottom');
			document.body.appendChild(this.dialog);
			this.anchor.style.position = 'relative';
			this.dialog.clonePosition(this.anchor, {
				'setWidth': false,
				'setHeight': false,
				'offsetTop': offsetTop,
				'offsetLeft': -3
				});
			this.dialog.style.zIndex = '99';
			this.panel.selectRange(this.originalRange.start, this.originalRange.end);
			this.panel.captureKeys();

			this.hidePickerListener = document.on('click', this.clickHandler.bindAsEventListener(this));
			this.pickerActive = true;
			Control.DatePicker.activePicker = this;
			this.pickerClicked();
		}
	}
});

/**
 * Control.DatePicker.activePicker -> Control.DatePicker
 *
 * A reference to the last opened date picker.
**/
Control.DatePicker.activePicker = null;

/**
 * Control.DatePicker.create(options) -> Element
 * - options (Hash): Additional options for the control.
 *
 * Creates a new date picker from scratch instead of transforming
 * an existing DOM element.  Returns the root element for the
 * date picker control, suitable for inserting into your page.
 * You can retrieve the Control.DatePicker instance behind the
 * returned element with `element.retrieve('datepicker')`.
 *
 * Options:
 *
 * * `className`: The CSS class to assign the &lt;input&gt; element
 * * `name`: The field name to assign the &lt;input&gt; element
 *
 * Additional options are passed through to `new Control.DatePicker()`.
 * See [[Control.DatePicker]] constructor for available options.
 *
 * Example:
 *
 * 	var dp = Control.DatePicker.create();
 * 	panel.appendChild(dp);
 * 	dp.open();
**/
Control.DatePicker.create = function(options) {
	options = Object.extend({
			'className': 'datepicker',
			'name': 'date'
		}, options || {});
	var elt = new Element('input', { 'class': options.className, 'name': name });
	var dp = new Control.DatePicker(elt);
	dp.wrapper.store('datepicker', dp);
	return dp.wrapper;
};

/**
 * class Control.DatePicker.i18n
 *
 * Internationalization settings for a [[Control.DatePicker]] instance.
**/
Control.DatePicker.i18n = Class.create();
Object.extend(Control.DatePicker.i18n, {
	available: ['cs_CZ', 'el_GR', 'fr_FR', 'it_IT', 'lt_LT', 'nl_NL', 'pl_PL', 'pt_BR', 'ru_RU'],
	baseLocales: {
		'us': {
			dateTimeFormat: 'MM-dd-yyyy HH:mm:ss',
			dateFormat: 'MM-dd-yyyy',
			firstWeekDay: 0,
			weekend: [0,6],
			timeFormat: 'HH:mm:ss'
		},
		'eu': {
			dateTimeFormat: 'dd-MM-yyyy HH:mm:ss',
			dateFormat: 'dd-MM-yyyy',
			firstWeekDay: 1,
			weekend: [0,6],
			timeFormat: 'HH:mm:ss'
		},
		'iso8601': {
			dateTimeFormat: 'yyyy-MM-dd HH:mm:ss',
			dateFormat: 'yyyy-MM-dd',
			firstWeekDay: 1,
			weekend: [0,6],
			timeFormat: 'HH:mm:ss'
		}
	},

/**
 * Control.DatePicker.i18n.createLocale(base, lang) -> Object
 * - base (String): The base locale (one of "us", "eu", "iso8601").
 * - lang (String): The language to use.
 *
 * Create a new locale combining a standard base locale ("us", "eu", "iso8601")
 * and a new language code.
**/
	createLocale: function(base, lang) {
		return Object.extend(Object.clone(Control.DatePicker.i18n.baseLocales[base]), {'language': lang});
	}
});
Control.DatePicker.i18n.prototype = {
/**
 * new Control.DatePicker.i18n([code])
 * - code (String): The locale code.  This can be a language code ("es")
 *   or a full locale ("es_AR").
 *
 * Create a new internationalization settings  based on the
 * specified locale code (i.e. "en_US").
 *
 * Locales that are supported by default are:
 *
 * * es
 * * en
 * * en_US
 * * en_GB
 * * de
 * * es_iso8601
 * * en_iso8601
 * * de_iso8601
 *
 * Additionally, there are other locales which are not included
 * but will be loaded on demand via an AJAX call if requested:
 *
 * * cs_CZ
 * * el_GR
 * * fr_FR
 * * it_IT
 * * lt_LT
 * * nl_NL
 * * pl_PL
 * * pt_BR
 * * ru_RU
 *
 * For details on creating new locales, see the
 * <a href="http://jongsma.org/software/protoplasm/datepicker#locales">Protoplasm
 * web site</a>.
**/
	initialize: function(code) {
		if (code)
			this.setLocale(code);
	},
	setLocale: function(code) {
		if (!(code in Control.DatePicker.Locale)
				&& Control.DatePicker.i18n.available.indexOf(code) > -1)
			throw("Locale available but not loaded");
		var lang = code.charAt(2) == '_' ? code.substring(0,2) : code;
		var locale = (Control.DatePicker.Locale[code] || Control.DatePicker.Locale[lang]);
		this.opts = Object.clone(locale || {});
		var language = locale ? Control.DatePicker.Language[locale.language] : null;
		if (language) Object.extend(this.opts, language);
	},
	opts: null,
	inheritOptions: function(options) {
		if (!this.opts) this.setLocale('en_US');
		return Object.extend(this.opts, options || {});
	},
/**
 * Control.DatePicker.i18n#tr(text) -> String
 * - text (String): The string to translate.
 *
 * Translates the given text into the language linked to
 * this instance.
**/
	tr: function(str) {
		return this.opts && this.opts.strings ? this.opts.strings[str] || str : str;
	}
};

/**
 * Control.DatePicker.Locale -> Hash
 *
 * Hash object that stores available locale definitions.
 *
 * Bundled locales: es, en, en\_US, en\_GB, de, es\_iso8601,
 * en\_iso8601, de\_iso8601
**/
Control.DatePicker.Locale = {};
with (Control.DatePicker) {
	// Full locale definitions not needed if countries use the language default format
	// Datepicker will fallback to the language default; i.e. 'es_AR' will use 'es'
	Locale['es'] = i18n.createLocale('eu', 'es');
	Locale['en'] = i18n.createLocale('us', 'en');
	Locale['en_GB'] = i18n.createLocale('eu', 'en');
	Locale['en_AU'] = Locale['en_GB'];
	Locale['de'] = i18n.createLocale('eu', 'de');
	Locale['es_iso8601'] = i18n.createLocale('iso8601', 'es');
	Locale['en_iso8601'] = i18n.createLocale('iso8601', 'en');
	Locale['de_iso8601'] = i18n.createLocale('iso8601', 'de');
}

/**
 * Control.DatePicker.Language -> Hash
 *
 * Hash object that stores available language definitions.
 *
 * Bundled languages: en, es, de
**/
Control.DatePicker.Language = {
	'es': {
		months: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
		days: ['Do', 'Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa'],
		strings: {
			'Now': 'Ahora',
			'Today': 'Hoy',
			'Time': 'Hora',
			'Exact minutes': 'Minuto exacto',
			'Select Date and Time': 'Selecciona Dia y Hora',
			'Select Time': 'Selecciona Hora',
			'Open calendar': 'Abre calendario'
		}
	},
	'de': { 
		months: ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'], 
		days: ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'], 
		strings: { 
			'Now': 'Jetzt', 
			'Today': 'Heute', 
			'Time': 'Zeit', 
			'Exact minutes': 'Exakte minuten', 
			'Select Date and Time': 'Zeit und Datum Auswählen',
			'Select Time': 'Zeit Auswählen',
			'Open calendar': 'Kalender öffnen'
		}
	}	
};

/**
 * class Control.DatePicker.Panel
 *
 * The dialog panel that is displayed when the date picker is opened.
**/
Control.DatePicker.Panel = Class.create(function() {

	function pad(x) {
		if (x < 10) return '0'+x;
		return new String(x);
	};

	return {
/**
 * new Control.DatePicker.Panel([options])
 * - options (Hash): Additional options for the panel.
 *
 * Create a new date picker panel.
 *
 * Additional options:
 *
 * * className: The CSS class of the panel element
 * * monthCount: The number of calendar months to display at one time
 * * layout: Layout mode for multiple calendars: 'horizontal' (default) or 'vertical'
 * * range: Use date range selection instead of single dates
 * * minDate: The minimum date that is allowed to be selected
 * * maxDate: The maximum date that is allowed to be selected
 * * timePicker: Display a time picker (default false) - <i>not
 *   compatible with "range" option</i>
 * * use24hrs: Show 24 hours in the time picker instead of
 *   AM/PM (default false)
 * * firstWeekDay: The first day of the week (default 0 - Sunday)
 * * weekend: An array of day numbers that are considered the
 *   weekend (default [0,6] - Saturday/Sunday)
 * * months: An array of 12 month names
 * * days: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
 * * closeOnToday: Close picker when the "Today" link is clicked
 *   (default true)
 * * selectToday: Automatically select today's date initially
**/
	initialize: function(options) {
		try {
			this.i18n = new Control.DatePicker.i18n(options && options.locale ? options.locale : 'en_US');
			options = this.i18n.inheritOptions(options);
		} catch(e) {
			this.i18n = new Control.DatePicker.i18n();
		}
		this.options = Object.extend({
						className: '',
						closeOnToday: true,
						selectToday: true,
						timePicker: false,
						use24hrs: false,
						firstWeekDay: 0,
						weekend: [0,6],
						months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
						days: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
					}, options || {});

		// Make sure first weekday is in the correct range
		with (this.options)
			if (isNaN(firstWeekDay*1)) firstWeekDay = 0;
			else firstWeekDay = firstWeekDay % 7;

		this.calendarCont = null;
		this.currentDate = this.options.date ? this.options.date : new Date();
		this.dayOfWeek = 0;
		this.minInterval = 5;

		this.rangeStart = this.currentDate;
		this.rangeEnd = this.options.dateEnd;
		this.inRange = false;
		this.position = this.options.position;
		this.selectedDays = [];

		this.currentDays = {};
		this.visibleDays = {};
		this.invisibleDays = {};

/**
 * Control.DatePicker.Panel#element -> Element
 *
 * The root Element of this dialog panel.
**/
		this.element = this.createPicker();
		this.selectDate(this.currentDate);

		this.element.on('selectstart', function(e) {
			Event.stop(e); }.bindAsEventListener(this));
	},

	createPicker: function() {
		var elt = new Element('div', {'class': '_pp_datepicker '+this.options.className});
		this.calendarCont = this.drawCalendar(elt, this.currentDate);

		Event.observe(elt, 'click', this.clickHandler.bindAsEventListener(this));
		this.keyListener = document.on('keydown', this.keyHandler.bindAsEventListener(this));
		document.on('click', function(e) {
				if (!e.findElement('._pp_datepicker'))
					this.keyListener.stop();
			}.bindAsEventListener(this));
		if (!this.options.captureKeys)
			this.keyListener.stop();
		
		return elt;
	},
	tr: function(str) {
		return this.i18n.tr(str);
	},
	captureKeys: function() {
		this.keyListener.start();
	},
	releaseKeys: function() {
		this.keyListener.stop();
	},
	setDate: function(date, recenter) {
		if (date) {
			// Clear container
			this.element.update();
			var dateKey = this.dateKey(date);
			if (!(dateKey in this.visibleDays)) {
				if (recenter)
					this.position = this.options.position;
				else if (date < this.currentDate)
					this.position = 'left';
				else if (date > this.currentDate)
					this.position = 'right';
				else
					this.position = this.options.position;
			}
			this.calendarCont = this.drawCalendar(this.element, date);
		}
	},
	drawCalendar: function(container, date) {
		var calendar = this.createCalendar(date);
		container.appendChild(calendar);
		container.style.width = calendar.style.width;
		if (!this.options.range && this.options.timePicker) {

			var selectListener = function(e) {
				if (this.options.onSelect)
					this.options.onSelect(this.currentDate);
				}.bindAsEventListener(this);

			var tp = new Control.TimePicker.Panel({
				'onChange': this.selectTime.bind(this),
				'onSelect': selectListener,
				'use24hrs': this.options.use24hrs
				});

			// Fuck this shit... how hard is it to get a centered shrink-to-fit
			// block that works in all browsers?
			//tp.element.style.display = 'inline-table';
			//tp.element.style.margin = '3px auto';
			var timewrap = new Element('table', {'style': 'margin: 3px auto;'});
			var row = timewrap.insertRow(0);
			var cell = $(row.insertCell(0));
			cell.appendChild(tp.element);
			container.appendChild(timewrap);

			tp.setTime(this.currentDate);
			this.timePicker = tp;

			var select = new Element('button').update(this.tr('Select Date and Time'));
			select.on('click', selectListener);
			container.appendChild(select);
		}
		return container;
	},
	createCalendar: function(date) {

		this.currentDays = {};
		this.visibleDays = {};
		this.invisibleDays = {};

		var wrapper = new Element('div');
		var header = this.createHeader(date);
		wrapper.appendChild(header);
		if ((months = this.options.monthCount) && months > 1) {
			if (months > 3)
				months = 3;
			// IE compatibility
			wrapper.style.width = (180*months + (months-1)*3) + 'px';
			var vertical = (this.options.layout == 'vertical');
			var row;
			if (!vertical) {
				var table = new Element('table', {'cellPadding': 0, 'cellSpacing': 0, 'border': 0});
				row = table.insertRow(0);
				wrapper.appendChild(table);
			}
			var start = new Date(date.getTime());
			start.setDate(1);
			if (this.position && this.position == 'left') {
				// Nothing, start is already fine
			} else if (this.position && this.position == 'right') {
				start.setMonth(start.getMonth() - (months - 1));
			} else {
				start.setMonth(start.getMonth() - Math.floor(months/2));
			}
			for (var i = 0; i < months; i++) {	
				var cal = this.createMonth(start);
				if (!vertical) {
					if (i > 0)
						cal.style.marginLeft = '3px';
				} else {
					if (i > 0)
						cal.style.marginTop = '3px';
				}
				if (!vertical) {
					var cell = $(row.insertCell(row.cells.length));
					cell.appendChild(cal);
				} else {
					wrapper.appendChild(cal);
				}
				start.setMonth(start.getMonth() + 1);
			}
		} else {
			// IE compatibility
			wrapper.style.width = '180px';
			wrapper.appendChild(this.createMonth(date));
		}

		return wrapper;
	},

	createHeader: function(date) {

		var today = new Date();
		var previousYear = new Date(date.getFullYear() - 1, date.getMonth(), 1)
		var previousMonth = new Date(date.getFullYear(), date.getMonth() - 1, 1)
		var nextMonth = new Date(date.getFullYear(), date.getMonth() + 1, 1)
		var nextYear = new Date(date.getFullYear() + 1, date.getMonth(), 1)

		var nav = new Element('div', {'class': '_pp_datepicker_navigation'});
		var link = new Element('span', {'class': '_pp_datepicker_previous',
			'title': this.monthName(previousYear.getMonth()) + ' '
				+ previousYear.getFullYear()}).update('&lt;&lt;');
		link.on('click', this.movePreviousYearListener());
		nav.insert(link);

		link = new Element('span', {'class': '_pp_datepicker_previous',
			'title': this.monthName(previousMonth.getMonth())+' '
				+previousMonth.getFullYear()}).update('&lt;');
		link.on('click', this.movePreviousMonthListener());
		nav.insert(link);

		link = new Element('span', {'class': '_pp_datepicker_next',
			'title': this.monthName(nextYear.getMonth())
				+ ' ' + nextYear.getFullYear()}).update('&gt;&gt;');
		link.on('click', this.moveNextYearListener());
		nav.insert(link);

		link = new Element('span', {'class': '_pp_datepicker_next',
			'title': this.monthName(nextMonth.getMonth())
				+ ' ' + nextMonth.getFullYear()}).update('&gt;');
		link.on('click', this.moveNextMonthListener());
		nav.insert(link);

		link = new Element('div', {'class': '_pp_datepicker_today',
			'title': today.getDate() + ' '
				+ this.monthName(today.getMonth()) + ' ' + today.getFullYear()}).update(
					this.options.timePicker ? this.tr('Now') : this.tr('Today'));
		link.on('click', this.clickedListener(today, true));
		nav.insert(link);

		return nav;
	},
	createMonth: function(date) {

		var table = new Element('table',
			{'cellSpacing': 0, 'cellPadding': 0, 'border': 0, 'class': '_pp_datepicker_table'});

		var row = $(table.insertRow(table.rows.length));
		if (this.options.range)
			row.insertCell(0);

		cell = $(row.insertCell(row.cells.length));
		cell.className = '_pp_title';
		cell.colSpan = 7;
		cell.update(this.monthName(date.getMonth()) + ' ' + date.getFullYear());

		row = $(table.insertRow(table.rows.length));
		if (this.options.range)
			row.insertCell(0);
		for (var i = 0; i < 7; ++i) {
			cell = new Element('th', {'width': '14%', 'class': '_pp_highlight'}
				).update(this.dayName((this.options.firstWeekDay + i) % 7));
			row.insert(cell);
		}
		
		var workDate = new Date(date.getFullYear(), date.getMonth(), 1);
		var day = workDate.getDay();

		// Pad with previous month
		if (day != this.options.firstWeekDay) {
			row = $(table.insertRow(table.rows.length));
			workDate.setDate(workDate.getDate() - ((day - this.options.firstWeekDay + 7) % 7));
			if (this.options.range) {
				cell = $(row.insertCell(row.cells.length));
				cell.className = '_pp_datepicker_weekselect';
				cell.on('mousedown', this.weekClicked(workDate));
			}
			day = workDate.getDay();
			while (workDate.getMonth() != date.getMonth()) {
				cell = new Element('td').update(workDate.getDate());
				this.assignDayClasses(cell, 'dayothermonth', workDate);
				cell.on('mousedown', this.rangeStartListener(workDate));
				cell.on('mouseover', this.hoverListener(workDate));
				cell.on('mouseup', this.rangeEndListener(workDate));

				var dateKey = this.dateKey(workDate);
				this.invisibleDays[dateKey] = cell;

				row.insert(cell);
				workDate.setDate(workDate.getDate() + 1);
				day = workDate.getDay();
			}
		}

		// Display days
		while (workDate.getMonth() == date.getMonth()) {
			if (day == this.options.firstWeekDay) {
				row = $(table.insertRow(table.rows.length));
				if (this.options.range) {
					if (this.options.range) {
						cell = new Element('td', {'class': '_pp_datepicker_weekselect'});
						cell.on('mousedown', this.weekClicked(workDate));
						row.insert(cell);
					}
				}
			}
			cell = new Element('td').update(workDate.getDate());
			this.assignDayClasses(cell, 'day', workDate);
			row.insert(cell);
			cell.on('mousedown', this.rangeStartListener(workDate));
			cell.on('mouseover', this.hoverListener(workDate));
			cell.on('mouseup', this.rangeEndListener(workDate));

			var dateKey = this.dateKey(workDate);
			this.visibleDays[dateKey] = cell;
			if (workDate.getFullYear() == this.currentDate.getFullYear()
					&& workDate.getMonth() == this.currentDate.getMonth())
				this.currentDays[dateKey] = cell;
			workDate.setDate(workDate.getDate() + 1);
			day = workDate.getDay();
		}

		// Pad with next month
		if (day != this.options.firstWeekDay)
			do {
				cell = new Element('td').update(workDate.getDate());
				this.assignDayClasses(cell, 'dayothermonth', workDate);
				row.insert(cell);
				var thisDate = new Date(workDate.getTime());
				cell.on('mousedown', this.rangeStartListener(workDate));
				cell.on('mouseover', this.hoverListener(workDate));
				cell.on('mouseup', this.rangeEndListener(workDate));

				var dateKey = this.dateKey(workDate);
				this.invisibleDays[dateKey] = cell;

				workDate.setDate(workDate.getDate() + 1);
				day = workDate.getDay();
			} while (workDate.getDay() != this.options.firstWeekDay);

		return table;
	},
	movePreviousMonthListener: function() {
		return function(e) {
				var d = this.currentDate;
				var prevMonth = new Date(d.getFullYear(), d.getMonth() - 1,
						d.getDate(), d.getHours(), d.getMinutes());
				if (prevMonth.getMonth() != (d.getMonth() + 11) % 12) prevMonth.setDate(0);
				this.selectDate(prevMonth, false, true);
			}.bindAsEventListener(this);
	},
	moveNextMonthListener: function() {
		return function(e) {
				var d = this.currentDate;
				var nextMonth = new Date(d.getFullYear(), d.getMonth() + 1,
						d.getDate(), d.getHours(), d.getMinutes());
				if (nextMonth.getMonth() != (d.getMonth() + 1) % 12) nextMonth.setDate(0);
				this.selectDate(nextMonth, false, true);
			}.bindAsEventListener(this);
	},
	moveNextYearListener: function() {
		return function(e) {
				var d = this.currentDate;
				var nextYear = new Date(d.getFullYear() + 1, d.getMonth(),
						d.getDate(), d.getHours(), d.getMinutes());
				if (nextYear.getMonth() != d.getMonth()) nextYear.setDate(0);
				this.selectDate(nextYear, false, true);
			}.bindAsEventListener(this);
	},
	movePreviousYearListener: function() {
		return function(e) {
				var d = this.currentDate;
				var prevYear = new Date(d.getFullYear() - 1, d.getMonth(),
						d.getDate(), d.getHours(), d.getMinutes());
				if (prevYear.getMonth() != d.getMonth()) prevYear.setDate(0);
				this.selectDate(prevYear, false, true);
			}.bindAsEventListener(this);
	},
	copyDate: function(d, timeOverride) {
		var d2 = new Date(d.getTime());
		var c = this.currentDate;
		if (!timeOverride) {
			d2.setHours(c.getHours());
			d2.setMinutes(c.getMinutes());
			d2.setSeconds(c.getSeconds());
			d2.setMilliseconds(c.getMilliseconds());
		}
		return d2;
	},
	rangeStartListener: function(date) {
		var d = this.copyDate(date);
		return function(e) {
			if (this.options.range) {
				if (this.dragging) return;
				this.dragging = true;
				this.dragged = false;
			}
			this.dateClicked(d);
		}.bindAsEventListener(this);
	},
	rangeEndListener: function(date) {
		var d = this.copyDate(date);
		return function(e) {
			if (this.options.range) {
				this.dragging = false;
				if (this.dragged)
					this.dateClicked(d);
			}
		}.bindAsEventListener(this);
	},
	hoverListener: function(date) {
		var d = this.copyDate(date);
		return function(e) {
			if (this.options.range && this.dragging) {
				this.dragged = true;
				this.dateClicked(d, true);
			}
		}.bindAsEventListener(this);
	},
	moveListener: function(date, timeOverride) {
		var d = this.copyDate(date, timeOverride);
		return function(e) {
				this.selectDate(d, false, true);
			}.bindAsEventListener(this);
	},
	clickedListener: function(date, timeOverride) {
		var d = this.copyDate(date, timeOverride);
		return function(e) {
				this.dateClicked(d);
			}.bindAsEventListener(this);
	},
	assignDayClasses: function(cell, baseClass, date) {
		cell = $(cell);
		var today = new Date();
		cell.addClassName(baseClass);
		if (date.getFullYear() == today.getFullYear()
				&& date.getMonth() == today.getMonth()
				&& date.getDate() == today.getDate())
			cell.addClassName('today');
		if (this.options.weekend.include(date.getDay()))
			cell.addClassName('weekend');
		if ((this.options.minDate && date < this.options.minDate)
				|| (this.options.maxDate && date > this.options.maxDate))
			cell.addClassName('disabled');
	},
	monthName: function(month) {
		return this.options.months[month];
	},
	dayName: function(day) {
		return this.options.days[day];
	},
	clickHandler: function(e) {
		this.captureKeys();
		if(this.options.onClick)
			this.options.onClick();
	},
	keyHandler: function(e) {
		var days = 0;
		switch (e.keyCode){
			case Event.KEY_RETURN:
				if (this.options.onSelect) this.options.onSelect(this.currentDate);
				break;
			case Event.KEY_LEFT:
				days = -1;
				break;
			case Event.KEY_UP:
				days = -7;
				break;
			case Event.KEY_RIGHT:
				days = 1;
				break;
			case Event.KEY_DOWN:
				days = 7;
				break;
			case 33: // PgUp
				var lastMonth = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() - 1, this.currentDate.getDate());
				days = -this.getDaysOfMonth(lastMonth);
				break;
			case 34: // PgDn
				days = this.getDaysOfMonth(this.currentDate);
				break;
			case 13: // enter-key (forms without submit buttons)
				this.dateClicked(this.currentDate);
				break;
			default:
				return;
		}
		if (days != 0) {
			var moveDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), this.currentDate.getDate() + days);
			moveDate.setHours(this.currentDate.getHours());
			moveDate.setMinutes(this.currentDate.getMinutes());
			moveDate.setSeconds(this.currentDate.getSeconds());
			moveDate.setMilliseconds(this.currentDate.getMilliseconds());
			this.selectDate(moveDate);
		}
		Event.stop(e);
		return false;
	},
	getDaysOfMonth: function(date) {
		var lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
		return lastDay.getDate();
	},
	getNextMonth: function(month, year, increment) {
		if (p_Month == 11) return [0, year + 1];
		else return [month + 1, year];
	},
	getPrevMonth: function(month, year, increment) {
		if (p_Month == 0) return [11, year - 1];
		else return [month - 1, year];
	},
	dateClicked: function(date, dragging) {
		if (date) {
			var endRange = this.inRange && !dragging;
			if (!dragging)
				this.inRange = false;
			this.selectDate(date, !endRange);
			if (this.options.onSelect) {
				if (this.options.range) {
					if (endRange && this.rangeStart) {
						if (this.rangeStart < this.rangeEnd)
							this.options.onSelect(this.rangeStart, this.rangeEnd);
						else
							this.options.onSelect(this.rangeEnd, this.rangeStart);
						this.dragging = false;
					}
				} else if (!this.options.timePicker)
					this.options.onSelect(date);
			}
			var dateKey = this.dateKey(date);
			if (!(dateKey in this.currentDays) || this.position != this.options.position) {
				this.position = this.options.position;
				//this.setDate(date);
			}
		}
	},
	dateKey: function(date) {
		return date.getFullYear() + pad(date.getMonth()) + pad(date.getDate());
	},
	applyClass: function(date, klass) {
		var k = this.dateKey(date);
		if (k in this.visibleDays)
			this.visibleDays[k].addClassName(klass);
		if (k in this.invisibleDays)
			this.invisibleDays[k].addClassName(klass);
	},
	weekClicked: function(first) {
		var start = new Date(first.getTime());
		var end = new Date(first.getTime());
		end.setDate(end.getDate() + 6);
		return function(e) {
			this.selectRange(start, end);
		}.bindAsEventListener(this);
	},
	selectRange: function(start, end) {
		this.inRange = false;
		this.dateClicked(start);
		if (this.options.range)
			this.dateClicked(end);
	},
	selectDate: function(date, startRange, noRange) {
		if (date) {

			if (this.options.minDate && date < this.options.minDate)
				date = this.options.minDate;
			else if (this.options.maxDate && date > this.options.maxDate)
				date = this.options.maxDate;

			this.currentDate = date;

			var dateKey = this.dateKey(date);
			if (!(dateKey in this.visibleDays)
					|| (noRange && !(dateKey in this.currentDays)))
				this.setDate(date, noRange);

			this.selectedDays.invoke('removeClassName', 'current');

			if (this.options.range) {
				this.selectedDays.invoke('removeClassName', 'leftrange');
				this.selectedDays.invoke('removeClassName', 'rightrange');
				this.selectedDays.invoke('removeClassName', 'currenthint');
				if (!noRange) {
					if (!this.inRange && startRange) {
						this.inRange = true;
						this.rangeStart = date;
					}
					this.rangeEnd = date;
				}
				this.selectedDays = [];
				if (this.rangeStart) {
					var low, high;
					if (this.rangeEnd < this.rangeStart) {
						low = new Date(this.rangeEnd.getFullYear(), this.rangeEnd.getMonth(), this.rangeEnd.getDate());
						high = new Date(this.rangeStart.getFullYear(), this.rangeStart.getMonth(), this.rangeStart.getDate());
					} else {
						low = new Date(this.rangeStart.getFullYear(), this.rangeStart.getMonth(), this.rangeStart.getDate());
						high = new Date(this.rangeEnd.getFullYear(), this.rangeEnd.getMonth(), this.rangeEnd.getDate());
					}
					this.applyClass(low, 'leftrange');
					if (low.getTime() != high.getTime())
						this.applyClass(high, 'rightrange');
					while (low.getTime() <= high.getTime()) {	
						var k = this.dateKey(low);
						if (k in this.visibleDays) {
							this.visibleDays[k].addClassName('current');
							this.selectedDays.push(this.visibleDays[k]);
						}
						if (k in this.invisibleDays) {
							this.invisibleDays[k].addClassName('currenthint');
							this.selectedDays.push(this.invisibleDays[k]);
						}
						low.setDate(low.getDate() + 1);
					}
				}
			} else {
				this.selectedDays.invoke('removeClassName', 'singlerange');
				this.visibleDays[dateKey].addClassName('singlerange');
				this.selectedDays = [this.visibleDays[dateKey]];
			}

			if (this.options.timePicker)
				this.timePicker.setTime(date);

			if (this.options.onHover) {
				if (this.options.range)
					this.options.onHover(this.rangeStart, this.rangeEnd);
				else
					this.options.onHover(date);
			}

		}
	},
	selectTime: function(time) {
		this.currentDate.setHours(time.getHours());
		this.currentDate.setMinutes(time.getMinutes());
		this.currentDate.setSeconds(time.getSeconds());
		this.currentDate.setMilliseconds(time.getMilliseconds());
		if (this.options.onHover)
			this.options.onHover(this.currentDate);
	}
	}
}());

/**
 * class Control.DatePicker.DateFormat
 *
 * A date formatting utility class.
**/
Control.DatePicker.DateFormat = Class.create({
	
/**
 * new Control.DatePicker.DateFormat(format)
 * - format (String): The format string (see [[Control.DatePicker.DateFormat.format]]).
 *
 * Create a new DateFormat object the uses the specified format string.
**/
	initialize: function(format) { this.format = format; },

/**
 * Control.DatePicker.DateFormat#parse(text) -> Date
 * - text (String): The text to parse into a Date.
 *
 * Attempt to parse a string into a Date object according to this
 * object's formatting rules.
**/
	parse: function(value) { return Control.DatePicker.DateFormat.parseFormat(value, this.format); },

/**
 * Control.DatePicker.DateFormat#format(date) -> String
 * - date (Date): The date to format.
 *
 * Format a date into a string according to this object's formatting
 * rules.
**/
	format: function(value) { return Control.DatePicker.DateFormat.format(value, this.format); }

});

Object.extend(Control.DatePicker.DateFormat, {
	MONTH_NAMES: ['January','February','March','April','May','June','July','August','September','October','November','December','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
	DAY_NAMES: ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
	LZ: function(x,l) {l=l||2;x=''+x;while(x.length<l)x='0'+x;return x},
	compareDates: function(date1,dateformat1,date2,dateformat2) {
		var d1=Control.DatePicker.DateFormat.parseFormat(date1,dateformat1);
		var d2=Control.DatePicker.DateFormat.parseFormat(date2,dateformat2);
		if (d1==0 || d2==0) return -1;
		else if (d1 > d2) return 1;
		return 0;
	},
/**
 * Control.DatePicker.DateFormat.format(date, format) ->  String
 * - date (Date): The date to format.
 * - format (String): The format definition.
 *
 * Convert a date to a string representation according to the specified
 * format string.
 *
 * Formatting tokens:
 * TODO
**/
	format: function(date,format) {
		var LZ = Control.DatePicker.DateFormat.LZ;
		var MONTH_NAMES = Control.DatePicker.DateFormat.MONTH_NAMES;
		var DAY_NAMES = Control.DatePicker.DateFormat.DAY_NAMES;
		format=format+"";
		var result="";
		var i_format=0;
		var c="";
		var token="";
		var y=date.getYear()+"";
		var M=date.getMonth()+1;
		var d=date.getDate();
		var E=date.getDay();
		var H=date.getHours();
		var m=date.getMinutes();
		var s=date.getSeconds();
		var S=date.getMilliseconds();
		var yyyy,yy,MMM,MM,dd,hh,h,mm,ss,ampm,HH,H,KK,K,kk,k;
		// Convert real date parts into formatted versions
		var value=new Object();
		if (y.length < 4) {y=""+(y-0+1900);}
		value["y"]=""+y;
		value["yyyy"]=y;
		value["yy"]=y.substring(2,4);
		value["M"]=M;
		value["MM"]=LZ(M);
		value["MMM"]=MONTH_NAMES[M-1];
		value["NNN"]=MONTH_NAMES[M+11];
		value["d"]=d;
		value["dd"]=LZ(d);
		value["E"]=DAY_NAMES[E+7];
		value["EE"]=DAY_NAMES[E];
		value["H"]=H;
		value["HH"]=LZ(H);
		if (H==0){value["h"]=12;}
		else if (H>12){value["h"]=H-12;}
		else {value["h"]=H;}
		value["hh"]=LZ(value["h"]);
		if (H>11){value["K"]=H-12;} else {value["K"]=H;}
		value["k"]=H+1;
		value["KK"]=LZ(value["K"]);
		value["kk"]=LZ(value["k"]);
		if (H > 11) { value["a"]="PM"; }
		else { value["a"]="AM"; }
		value["m"]=m;
		value["mm"]=LZ(m);
		value["s"]=s;
		value["ss"]=LZ(s);
		value["S"]=S;
		value["SS"]=LZ(S,2);
		value["SSS"]=LZ(S,3);
		while (i_format < format.length) {
			c=format.charAt(i_format);
			token="";
			while ((format.charAt(i_format)==c) && (i_format < format.length))
				token += format.charAt(i_format++);
			if (value[token] != null) result += value[token];
			else result += token;
		}
		return result;
	},
	_isInteger: function(val) {
		var digits="1234567890";
		for (var i=0; i < val.length; i++)
			if (digits.indexOf(val.charAt(i))==-1) return false;
		return true;
	},
	_getInt: function(str,i,minlength,maxlength) {
		for (var x=maxlength; x>=minlength; x--) {
			var token=str.substring(i,i+x);
			if (token.length < minlength) return null;
			if (Control.DatePicker.DateFormat._isInteger(token)) return token;
		}
		return null;
	},
	parseFormat: function(val,format) {
		var LZ = Control.DatePicker.DateFormat.LZ;
		var MONTH_NAMES = Control.DatePicker.DateFormat.MONTH_NAMES;
		var DAY_NAMES = Control.DatePicker.DateFormat.DAY_NAMES;
		var _getInt = Control.DatePicker.DateFormat._getInt;
		val=val+"";
		format=format+"";
		var i_val=0;
		var i_format=0;
		var c="";
		var token="";
		var token2="";
		var x,y;
		var now=new Date();
		var year=now.getYear();
		var month=now.getMonth()+1;
		var date=1;
		var hh=now.getHours();
		var mm=now.getMinutes();
		var ss=now.getSeconds();
		var SS=now.getMilliseconds();
		var ampm="";
		
		while (i_format < format.length) {
			// Get next token from format string
			c=format.charAt(i_format);
			token="";
			while ((format.charAt(i_format)==c) && (i_format < format.length))
				token += format.charAt(i_format++);
			// Extract contents of value based on format token
			if (token=="yyyy" || token=="yy" || token=="y") {
				if (token=="yyyy") x=4;y=4;
				if (token=="yy") x=2;y=2;
				if (token=="y") x=2;y=4;
				year=_getInt(val,i_val,x,y);
				if (year==null) return 0;
				i_val += year.length;
				if (year.length==2) {
					if (year > 70) year=1900+(year-0);
					else year=2000+(year-0);
				}
			} else if (token=="MMM"||token=="NNN") {
				month=0;
				for (var i=0; i<MONTH_NAMES.length; i++) {
					var month_name=MONTH_NAMES[i];
					if (val.substring(i_val,i_val+month_name.length).toLowerCase()==month_name.toLowerCase()) {
						if (token=="MMM"||(token=="NNN"&&i>11)) {
							month=i+1;
							if (month>12) month -= 12;
							i_val += month_name.length;
							break;
						}
					}
				}
				if ((month < 1)||(month>12)) return 0;
			} else if (token=="EE"||token=="E") {
				for (var i=0; i<DAY_NAMES.length; i++) {
					var day_name=DAY_NAMES[i];
					if (val.substring(i_val,i_val+day_name.length).toLowerCase()==day_name.toLowerCase()) {
						i_val += day_name.length;
						break;
					}
				}
			} else if (token=="MM"||token=="M") {
				month=_getInt(val,i_val,token.length,2);
				if(month==null||(month<1)||(month>12)) return 0;
				i_val+=month.length;
			} else if (token=="dd"||token=="d") {
				date=_getInt(val,i_val,token.length,2);
				if(date==null||(date<1)||(date>31)) return 0;
				i_val+=date.length;
			} else if (token=="hh"||token=="h") {
				hh=_getInt(val,i_val,token.length,2);
				if(hh==null||(hh<1)||(hh>12)) return 0;
				i_val+=hh.length;
			} else if (token=="HH"||token=="H") {
				hh=_getInt(val,i_val,token.length,2);
				if(hh==null||(hh<0)||(hh>23)) return 0;
				i_val+=hh.length;
			} else if (token=="KK"||token=="K") {
				hh=_getInt(val,i_val,token.length,2);
				if(hh==null||(hh<0)||(hh>11)) return 0;
				i_val+=hh.length;
			} else if (token=="kk"||token=="k") {
				hh=_getInt(val,i_val,token.length,2);
				if(hh==null||(hh<1)||(hh>24)) return 0;
				i_val+=hh.length;hh--;
			} else if (token=="mm"||token=="m") {
				mm=_getInt(val,i_val,token.length,2);
				if(mm==null||(mm<0)||(mm>59)) return 0;
				i_val+=mm.length;
			} else if (token=="ss"||token=="s") {
				ss=_getInt(val,i_val,token.length,2);
				if(ss==null||(ss<0)||(ss>59)) return 0;
				i_val+=ss.length;
			} else if (token=="SS"||token=="S"||token=="SSS") {
				SS=_getInt(val,i_val,token.length,3);
				if(SS==null||(SS<0)||(SS>999)) return 0;
				i_val+=SS.length;
			} else if (token=="a") {
				if (val.substring(i_val,i_val+2).toLowerCase()=="am") ampm="AM";
				else if (val.substring(i_val,i_val+2).toLowerCase()=="pm") ampm="PM";
				else return 0;
				i_val+=2;
			} else {
				if (val.substring(i_val,i_val+token.length)!=token) return 0;
				else i_val+=token.length;
			}
		}
		// If there are any trailing characters left in the value, it doesn't match
		if (i_val != val.length) return 0;
		// Is date valid for month?
		if (month==2) {
			// Check for leap year
			if (((year%4==0)&&(year%100 != 0)) || (year%400==0)) { // leap year
				if (date > 29) return 0;
			} else if (date > 28) {
				return 0;
			}
		}
		if ((month==4)||(month==6)||(month==9)||(month==11))
			if (date > 30) return 0;
		// Correct hours value
		if (hh<12 && ampm=="PM") hh=hh-0+12;
		else if (hh>11 && ampm=="AM") hh-=12;
		var newdate=new Date(year,month-1,date,hh,mm,ss,SS);
		return newdate;
	},
/**
 * Control.DatePicker.DateFormat.parse(date[, format]) -> Date
 * - text (String): The text to parse.
 * - format (String): The format definition to match against.
 *
 * Attempt to parse a string to a Date, given the specified
 * format string.  If `format` is omitted, DateFormat will
 * try some common formats.
 *
 * See [[Control.DatePicker.DateFormat.format]] for formatting string details.
**/
	parse: function(val, format) {
		if (format) {
			return Control.DatePicker.DateFormat.parseFormat(val, format);
		} else {
			var generalFormats=['y-M-d','MMM d, y','MMM d,y','y-MMM-d','d-MMM-y','MMM d'];
			var monthFirst=['M/d/y','M-d-y','M.d.y','MMM-d','M/d','M-d'];
			var dateFirst =['d/M/y','d-M-y','d.M.y','d-MMM','d/M','d-M'];
			var checkList=[generalFormats,monthFirst,dateFirst];
			var d=null;
			for (var i=0; i<checkList.length; i++) {
				var l=checkList[i];
				for (var j=0; j<l.length; j++) {
					d=Control.DatePicker.DateFormat.parseFormat(val,l[j]);
					if (d!=0) return new Date(d);
				}
			}
			return null;
		}
	}
});

Protoplasm.register('datepicker', Control.DatePicker);
