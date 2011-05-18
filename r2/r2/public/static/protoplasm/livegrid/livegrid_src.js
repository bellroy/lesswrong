if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize livegrid');
if (window.Control == undefined) Control = {};

Protoplasm.loadStylesheet('livegrid.css', 'livegrid');

/**
 * class Control.LiveGrid
 * 
 * Transforms a table into a dynamically updating, scrolling viewport
 * that can be populated via AJAX queries.
 *
 * Example: <a href="http://jongsma.org/software/protoplasm/control/livegrid">Live
 * Grid demo</a>
**/
Control.LiveGrid = Class.create({

	initialize: function(table, visibleRows, totalRows, fetchHandler, options) {

		if (options == null) options = {};

		this.table = $(table);

		if (lg = this.table.retrieve('livegrid'))
			throw('This table is already a Live Grid');

		this.fetchHandler = fetchHandler;
		this.sortField = options.sortField ? options.sortField : null;
		this.sortDir = options.sortDir ? options.sortDir : null;

		// Create core components
		var columnCount = this.table.rows[0].cells.length
		this.metaData = new Control.LiveGrid.MetaData(visibleRows, totalRows, columnCount, options);
		this.buffer   = new Control.LiveGrid.Buffer(this.metaData);
		this.viewPort = new Control.LiveGrid.ViewPort(this.table, this.buffer, this.metaData);
		this.scroller = new Control.LiveGrid.Scroller(this.viewPort, this.metaData, this.requestContentRefresh.bind(this));

		// Create optional components
		if (options.selectable)
			this.selector = new Control.LiveGrid.Selector(this.table, this.fetchHandler, this.metaData);
		if (options.sortHeader)
			this.sorter   = new Control.LiveGrid.Sort(options.sortHeader, this.metaData, this.sort.bind(this));

		if (options.captureKeyEvents) this.captureKeys();
	
		this.processingRequest = null;
		this.unprocessedRequest = null;

		// Pre-fetch data into the buffer
		if (options.prefetchBuffer || options.offset > 0) {
			var offset = 0;
			if (options.offset) {
				offset = options.offset;			
				this.scroller.moveScroll(offset);
				this.viewPort.scrollTo(this.scroller.rowToPixel(offset));			
			}
			//alert('2: requestContentRefresh');
			this.requestContentRefresh(offset);
		}

		this.table.store('livegrid', this)
	},

	resetContents: function() {
		this.scroller.unplug();
		this.scroller.moveScroll(0);
		this.scroller.plugin();
		this.buffer.clear();
		this.viewPort.clearContents();
	},

	captureKeys: function() {
		this.keyObserver = this.keyEvent.bindAsEventListener(this);
		Event.observe(window, 'keypress', this.keyObserver);
	},

	releaseKeys: function() {
		Event.stopObserving(window, 'keypress', this.keyObserver);
	},

	keyEvent: function(e) {
		if (e.keyCode == Event.KEY_DOWN) {
			this.moveSelection(e, 1);
		} else if (e.keyCode == Event.KEY_UP) {
			this.moveSelection(e, -1);
		} else if (e.keyCode == Event.KEY_RETURN && e.shiftKey) {
			this.selector.rowdblclickhandler()(e);
		} else if (e.keyCode == 33) { // PgUp
			this.moveSelection(e, -this.metaData.pageSize);
		} else if (e.keyCode == 34) { // PgDn
			this.moveSelection(e, this.metaData.pageSize);
		//} else if (e.keyCode == 36) { // Home
		//	this.moveSelection(e, -this.metaData.totalRows);
		//} else if (e.keyCode == 35) { // End
		//	this.moveSelection(e, this.metaData.totalRows);
		}
	},

	moveSelection: function(e, rows) {
		var maxTop = this.metaData.totalRows - this.metaData.pageSize;
		if (maxTop < 0) maxTop = 0;

		if (this.selector) {
			var lastRow = (e.shiftKey && this.selector.previousSelections != null
					? this.selector.lastRangeSelected
					: this.selector.lastRowSelected);
			if (lastRow == null) lastRow = -1;
			if (lastRow + rows >= this.metaData.totalRows)
				rows = (this.metaData.totalRows - lastRow) - 1;
			else if (lastRow + rows < 0)
				rows = -lastRow;

			var currentOffset = this.selector.currentOffset;
			var newRow = lastRow + rows;

			// Scroll view
			if (newRow - currentOffset >= this.metaData.getPageSize() || newRow - currentOffset < 0) {
				var newOffset = currentOffset + rows;
				if (newOffset > maxTop) {
					newOffset = maxTop;
					newRow = lastRow + (maxTop - newOffset);
				} else if (newOffset < 0) {
					newRow = 0;
					newOffset = 0;
				}
				this.scroller.moveScroll(newOffset);
			}
			this.selector.rowmousedownhandler.bind(this.selector)(newRow - currentOffset)(e);
		} else {
			// Just scroll view
			var currentOffset = parseInt(this.scroller.scrollerDiv.scrollTop / this.viewPort.rowHeight);
			var newOffset = currentOffset + rows;
			if (newOffset > maxTop) newOffset = maxTop;
			this.scroller.moveScroll(newOffset);
		}
	},

	sort: function(field, direction) {
		this.sortField = field;
		this.sortDir = direction;
		this.refresh();
	},

	refresh: function() {
		this.resetContents();
		//alert('3: requestContentRefresh');
		this.requestContentRefresh(0);
		if (this.selector) this.selector.deselectAllRows();
	},

	setTotalRows: function(newTotalRows) {
		this.metaData.setTotalRows(newTotalRows);
		this.viewPort.setPageSize(this.metaData.getPageSize());
		this.scroller.updateSize();
		if (this.selector)
			this.selector.applyRowBehavior();
	},

	handleTimedOut: function() {
		//server did not respond in 4 seconds... assume that there could have been
		//an error or something, and allow requests to be processed again...
		this.processingRequest = null;
		this.processQueuedRequest();
	},

	fetchBuffer: function(offset) {
		if (this.buffer.isInRange(offset) &&
			!this.buffer.isNearingLimit(offset)) {
			return;
		}

		if (this.processingRequest) {
			this.unprocessedRequest = new Control.LiveGrid.Request(offset);
			return;
		}

		var bufferStartPos = this.buffer.getFetchOffset(offset);
		this.processingRequest = new Control.LiveGrid.Request(offset);
		this.processingRequest.bufferOffset = bufferStartPos;
		var fetchSize = this.buffer.getFetchSize(offset);
		var partialLoaded = false;

		this.fetchHandler(bufferStartPos, fetchSize, this.sortField, this.sortDir, this.updateData.bind(this));
		
		this.timeoutHandler = setTimeout(this.handleTimedOut.bind(this), 20000); //todo: make as option
	},

	requestContentRefresh: function(contentOffset) {
		this.fetchBuffer(contentOffset);
	},

	updateData: function(response) {
		try {
			clearTimeout(this.timeoutHandler);
			this.buffer.update(response, this.processingRequest.bufferOffset);
			this.viewPort.bufferChanged();
		}
		catch(err) {}
		finally {this.processingRequest = null; }
		this.processQueuedRequest();
	},

	processQueuedRequest: function() {
		if (this.unprocessedRequest != null) {
			//alert('1: requestContentRefresh');
			this.requestContentRefresh(this.unprocessedRequest.requestOffset);
			this.unprocessedRequest = null;
		}
	}
});

// Helper function to allow using LiveGrid functionality with pre-loaded data
Control.LiveGrid.staticFetchHandler = function(rowdata, columns) {
	var sortedRows = Control.LiveGrid.convertToLiveGridRows(rowdata, columns);
	return function(offset, limit, sortField, sortDir, callback) {
		// Sort is needed
		if (sortField) {
			var sortIndex = -1;
			for (var i = 0; i < columns.length; ++i) {
				if (columns[i] == sortField) {
					sortIndex = i;
					break;
				}
			}
			if (sortIndex > -1) {
				sortedRows = sortedRows.sort(
						function(a, b) {
							var ac = a.columns[sortIndex];
							var bc = b.columns[sortIndex];
							if (ac < bc) return (sortDir.toLowerCase() == 'desc' ? 1 : -1);
							else if (ac == bc) return 0;
							else if (ac > bc) return (sortDir.toLowerCase() == 'desc' ? -1 : 1);
						}
					);
			}
		}
		// Get sub-array
		if (offset >= sortedRows.length) offset = sortedRows.length - 1;
		if (offset + limit > sortedRows.length) limit = sortedRows.length - offset;
		callback(sortedRows.slice(offset, offset + limit));
	};
};

Control.LiveGrid.convertToLiveGridRows = function(rows, tableCols) {
	var rowdata = Array();
	if (rows.length) {
		for (var i = 0; i < rows.length; ++i) {
			rowdata[i] = { id: rows[i].id, columns: new Array() };
			for (var j = 0; j < tableCols.length; ++j)
				rowdata[i].columns[j] = rows[i][tableCols[j]];
		}
	} else {
		rowdata[0] = { id: rows.id, columns: new Array() };
		for (var j = 0; j < tableCols.length; ++j)
			rowdata[0].columns[j] = rows[tableCols[j]];
	}
	return rowdata;
};
// Control.LiveGrid.MetaData -----------------------------------------------------

Control.LiveGrid.MetaData = Class.create({

	initialize: function(pageSize, totalRows, columnCount, options) {
		this.pageSize = pageSize;
		this.totalRows = totalRows;
		this.setOptions(options);
		this.scrollArrowHeight = 16;
		this.columnCount = columnCount;
	},

	setOptions: function(options) {
		this.options = Object.extend({
			largeBufferSize: 7.0,	// 7 pages
			nearLimitFactor: 0.2	// 20% of buffer
		}, options || {});
	},

	getPageSize: function() {
		return this.totalRows < this.pageSize ? this.totalRows : this.pageSize;
	},

	getTotalRows: function() {
		return this.totalRows;
	},

	setTotalRows: function(n) {
		this.totalRows = n;
	},

	getLargeBufferSize: function() {
		return parseInt(this.options.largeBufferSize * this.pageSize);
	},

	getLimitTolerance: function() {
		return parseInt(this.getLargeBufferSize() * this.options.nearLimitFactor);
	}
});

// Control.LiveGrid.Scroller -----------------------------------------------------

Control.LiveGrid.Scroller = Class.create({

	initialize: function(viewPort, metaData, scrollHandler) {
		this.metaData = metaData;
		this.viewPort = viewPort;
		this.scrollHandler = scrollHandler;

		this.isIE = navigator.userAgent.toLowerCase().indexOf("msie") >= 0;
		this.createScrollBar();
		this.scrollTimeout = null;
		this.rows = new Array();
	},

	isUnPlugged: function() {
		return this.scrollerDiv.onscroll == null;
	},

	plugin: function() {
		this.scrollerDiv.onscroll = this.handleScroll.bindAsEventListener(this);
	},

	unplug: function() {
		this.scrollerDiv.onscroll = null;
	},

	createScrollBar: function() {
		var visibleHeight = this.viewPort.visibleHeight();
		// create the outer div...
		this.scrollerDiv = document.createElement("div");
		var scrollerStyle = this.scrollerDiv.style;
		scrollerStyle.position = "relative";
		scrollerStyle.left = this.isIE ? "-6px" : "-3px";
		scrollerStyle.width = "19px";
		scrollerStyle.height = visibleHeight + "px";
		scrollerStyle.overflow = "auto";

		// create the inner div...
		this.heightDiv = document.createElement("div");
		this.heightDiv.style.width = "1px";

		this.heightDiv.style.height = parseInt(visibleHeight *
								this.metaData.getTotalRows()/this.metaData.getPageSize()) + "px" ;
		this.scrollerDiv.appendChild(this.heightDiv);
		//this.scrollerDiv.onscroll = this.handleScroll.bindAsEventListener(this);

		var table = this.viewPort.table;
		table.parentNode.parentNode.insertBefore(this.scrollerDiv, table.parentNode.nextSibling);

		// Activate scrollbar (needs to be delayed to prevent immediate firing
		// of onscroll event - don't ask me why)
		setTimeout(this.plugin.bind(this));
	},

	updateSize: function() {
		var table = this.viewPort.table;
		var visibleHeight = this.viewPort.visibleHeight();
		this.scrollerDiv.style.height = visibleHeight + 'px';
		if (this.metaData.getPageSize() == 0)
			this.heightDiv.style.height = 0;
		else
			this.heightDiv.style.height = parseInt(visibleHeight * this.metaData.getTotalRows()/this.metaData.getPageSize()) + "px";
	},

	rowToPixel: function(rowOffset) {
		return (rowOffset / this.metaData.getTotalRows()) * this.heightDiv.offsetHeight
	},

	moveScroll: function(rowOffset) {	
		var offset = this.metaData.totalRows == 0 ? 0 : rowOffset;
		if (this.metaData.options.onbeforescroll)
			this.metaData.options.onbeforescroll(rowOffset, this.metaData.getPageSize(), this.metaData.totalRows);
		this.scrollerDiv.scrollTop = this.rowToPixel(rowOffset);
		if (this.metaData.options.onscroll)
			this.metaData.options.onscroll(rowOffset, this.metaData.getPageSize(), this.metaData.totalRows);
	},

	handleScroll: function() {
		if (this.scrollTimeout)
			clearTimeout(this.scrollTimeout);

		var contentOffset = parseInt(this.scrollerDiv.scrollTop / this.viewPort.rowHeight);

		if (this.metaData.options.onbeforescroll)
			this.metaData.options.onbeforescroll(contentOffset, this.metaData.getPageSize(), this.metaData.totalRows);

		//alert('4: requestContentRefresh');
		this.scrollHandler(contentOffset);
		this.viewPort.scrollTo(this.scrollerDiv.scrollTop);
	
		if (this.metaData.options.onscroll)
			this.metaData.options.onscroll(contentOffset, this.metaData.getPageSize(), this.metaData.totalRows);

		this.scrollTimeout = setTimeout(this.scrollIdle.bind(this), 1200);
	},

	scrollIdle: function() {
		if (this.metaData.options.onscrollidle)
			this.metaData.options.onscrollidle();
	}
});

// Control.LiveGrid.Buffer -----------------------------------------------------

Control.LiveGrid.Buffer = Class.create({

	initialize: function(metaData, viewPort) {
		this.startPos = 0;
		this.size = 0;
		this.metaData = metaData;
		this.rows = new Array();
		this.updateInProgress = false;
		this.viewPort = viewPort;
		this.maxBufferSize = metaData.getLargeBufferSize() * 2;
		this.maxFetchSize = metaData.getLargeBufferSize();
		this.lastOffset = 0;
	},

	getBlankRow: function() {
		if (!this.blankRow) {
			this.blankRow = new Array();
			for (var i=0; i < this.metaData.columnCount ; i++)
				this.blankRow[i] = "&nbsp;";
		}
		return this.blankRow;
	},

	fixRows: function(response) {
		for (var i=0; i < response.length; ++i)
			for (var j=0; j < response[i].columns.length; ++j)
				if (!response[i].columns[j]) response[i].columns[j] = '&nbsp;';
		return response;
	},
	
	update: function(response, start) {
		var newRows = this.fixRows(response);
		if (this.rows.length == 0) { // initial load
			this.rows = newRows;
			this.size = this.rows.length;
			this.startPos = start;
			return;
		}
		if (start > this.startPos) { //appending
			if (this.startPos + this.rows.length < start) {
				this.rows =	newRows;
				this.startPos = start;//
			} else {
					this.rows = this.rows.concat(newRows.slice(0, newRows.length));
				if (this.rows.length > this.maxBufferSize) {
					var fullSize = this.rows.length;
					this.rows = this.rows.slice(this.rows.length - this.maxBufferSize, this.rows.length)
					this.startPos = this.startPos +	(fullSize - this.rows.length);
				}
			}
		} else { //prepending
			if (start + newRows.length < this.startPos) {
				this.rows =	newRows;
			} else {
				this.rows = newRows.slice(0, this.startPos).concat(this.rows);
				if (this.rows.length > this.maxBufferSize)
					this.rows = this.rows.slice(0, this.maxBufferSize)
			}
			this.startPos =	start;
		}
		this.size = this.rows.length;
	},

	clear: function() {
		this.rows = new Array();
		this.startPos = 0;
		this.size = 0;
	},

	isOverlapping: function(start, size) {
		return ((start < this.endPos()) && (this.startPos < start + size)) || (this.endPos() == 0)
	},

	isInRange: function(position) {
		return (position >= this.startPos) && (position + this.metaData.getPageSize() <= this.endPos());
				//&& this.size() != 0;
	},

	isNearingTopLimit: function(position) {
		return position - this.startPos < this.metaData.getLimitTolerance();
	},

	endPos: function() {
		return this.startPos + this.rows.length;
	},

	isNearingBottomLimit: function(position) {
		return this.endPos() - (position + this.metaData.getPageSize()) < this.metaData.getLimitTolerance();
	},

	isAtTop: function() {
		return this.startPos == 0;
	},

	isAtBottom: function() {
		return this.endPos() == this.metaData.getTotalRows();
	},

	isNearingLimit: function(position) {
		return (!this.isAtTop() && this.isNearingTopLimit(position)) ||
			(!this.isAtBottom() && this.isNearingBottomLimit(position))
	},

	getFetchSize: function(offset) {
		var adjustedOffset = this.getFetchOffset(offset);
		var adjustedSize = 0;
		if (adjustedOffset >= this.startPos) { //apending
			var endFetchOffset = this.maxFetchSize	+ adjustedOffset;
			if (endFetchOffset > this.metaData.totalRows)
				endFetchOffset = this.metaData.totalRows;
			adjustedSize = endFetchOffset - adjustedOffset;
		} else {//prepending
			var adjustedSize = this.startPos - adjustedOffset;
			if (adjustedSize > this.maxFetchSize)
				adjustedSize = this.maxFetchSize;
		}
		return adjustedSize;
	},

	getFetchOffset: function(offset) {
		var adjustedOffset = offset;
		if (offset > this.startPos)	//apending
			adjustedOffset = (offset > this.endPos()) ? offset :	this.endPos();
		else { //prepending
			if (offset + this.maxFetchSize >= this.startPos) {
				var adjustedOffset = this.startPos - this.maxFetchSize;
				if (adjustedOffset < 0)
					adjustedOffset = 0;
			}
		}
		this.lastOffset = adjustedOffset;
		return adjustedOffset;
	},

	getRows: function(start, count) {
		var begPos = start - this.startPos
		var endPos = begPos + count

		// er? need more data...
		if (endPos > this.size)
			endPos = this.size;

		var results = new Array()
		var index = 0;
		for (var i=begPos ; i < endPos; i++)
			results[index++] = this.rows[i];

		return results;
	},

	convertSpaces: function(s) {
		return s.split(" ").join("&nbsp;");
	}

});


//Control.LiveGrid.ViewPort --------------------------------------------------
Control.LiveGrid.ViewPort = Class.create({

	initialize: function(table, buffer, metaData) {

		this.metaData = metaData;
		this.table = table;
		this.buffer = buffer;

		this.setPageSize(metaData.getPageSize());

		this.rowTemplate = null;
		this.lastDisplayedStartPos = 0;
		this.lastPixelOffset = 0;
		this.startPos = 0;
	},

	setPageSize: function(rows) {
		this.fillTableRows(this.table, rows);

		this.div = this.table.parentNode;
		this.rowHeight = rows > 0 ? this.table.offsetHeight / rows : 1;
		this.div.style.height = this.table.offsetHeight + 'px';
		this.div.style.overflow = "hidden";

		// Add an extra row to simulate smooth scrolling
		this.visibleRows = rows > 0 ? rows + 1 : 0;
		this.fillTableRows(this.table, this.visibleRows);
		this.setOddOrEven(this.table, 0);
	},

	fillTableRows: function(table, rows) {
		// Make sure there's something to clone
		if (table.rows.length || this.rowTemplate) {
			if (!this.rowTemplate) {
				this.rowTemplate = table.rows[0];
				for (var i = 0; i < this.rowTemplate.cells.length; ++i) {
					if (!this.rowTemplate.cells[i].innerHTML)
						// Put some data in row to force it to expand to actual height
						this.rowTemplate.cells[i].innerHTML = '&nbsp;';
				}
			}
			// Add more rows if user only provided a single template row
			while (table.rows.length < rows) {
				var newRow = table.insertRow(table.rows.length);
				newRow.className = this.rowTemplate.className;
				for (j = 0; j < this.rowTemplate.cells.length; ++j) {
					var cell = newRow.insertCell(newRow.cells.length);
					if (this.rowTemplate.cells[j].className)
						cell.className = this.rowTemplate.cells[j].className;
					if (this.rowTemplate.cells[j].width)
						cell.width = this.rowTemplate.cells[j].width;
					if (this.rowTemplate.cells[j].style.width)
						cell.style.width = this.rowTemplate.cells[j].style.width;
					// Put some data in row to force it to expand to actual height
					cell.innerHTML = '&nbsp;';
				}
			}
			while (table.rows.length > rows) {
				table.deleteRow(table.rows.length - 1);
			}
		}
	},

	setOddOrEven: function(table, offset) {
		for (var i = 0; i < table.rows.length; ++i) {
			if (i % 2 == 1) {
				Element.removeClassName(table.rows[i], 'even');
				Element.addClassName(table.rows[i], 'odd');
			} else {
				Element.removeClassName(table.rows[i], 'odd');
				Element.addClassName(table.rows[i], 'even');
			}
		}
	},

	populateRow: function(htmlRow, row) {
		// Avoid overflows from passing in too long of an array
		var rowLength = htmlRow.cells.length;
		var columns = row.columns ? row.columns : row;
		if (row.id) htmlRow.id = this.metaData.options.rowIdPrefix ? this.metaData.options.rowIdPrefix + row.id : row.id;
		for (var j=0; j < rowLength; j++) {
			// Make up for IE being retarded
			//htmlRow.cells[j].innerHTML = '<div>' + columns[j] + '</div>';
			htmlRow.cells[j].innerHTML = columns[j];
		}
	},

	bufferChanged: function() {
		this.refreshContents(parseInt(this.lastPixelOffset / this.rowHeight));
	},

	clearRows: function() {
		if (!this.isBlank) {
			for (var i=0; i < this.visibleRows; i++)
				this.populateRow(this.table.rows[i], this.buffer.getBlankRow());
			this.isBlank = true;
		}
	},

	clearContents: function() {
		this.clearRows();
		this.scrollTo(0);
		this.startPos = 0;
		this.lastStartPos = -1;
	},

	refreshContents: function(startPos) {
		if (startPos == this.lastRowPos && !this.isPartialBlank && !this.isBlank)
			return;

		if ((startPos + this.visibleRows < this.buffer.startPos)
			|| (this.buffer.startPos + this.buffer.size < startPos)
			|| (this.buffer.size == 0)) {
			this.clearRows();
			return;
		}
		this.isBlank = false;
		var viewPrecedesBuffer = this.buffer.startPos > startPos
		var contentStartPos = viewPrecedesBuffer ? this.buffer.startPos: startPos;

		var contentEndPos = (this.buffer.startPos + this.buffer.size < startPos + this.visibleRows)
											? this.buffer.startPos + this.buffer.size
											: startPos + this.visibleRows;
		var rowSize = contentEndPos - contentStartPos;
		var rows = this.buffer.getRows(contentStartPos, rowSize);
		var blankSize = this.visibleRows - rowSize;
		var blankOffset = viewPrecedesBuffer ? 0: rowSize;
		var contentOffset = viewPrecedesBuffer ? blankSize: 0;

		// Initialize what we have
		for (var i=0; i < rows.length; i++)
			this.populateRow(this.table.rows[i + contentOffset], rows[i]);

		// Blank out the rest
		for (var i=0; i < blankSize; i++)
			this.populateRow(this.table.rows[i + blankOffset], this.buffer.getBlankRow());

		this.isPartialBlank = blankSize > 0;
		this.lastRowPos = startPos;
	},

	scrollTo: function(pixelOffset) {	
		if (this.lastPixelOffset == pixelOffset)
			return;

		this.refreshContents(parseInt(pixelOffset / this.rowHeight))
		this.div.scrollTop = pixelOffset % this.rowHeight		
	
		this.lastPixelOffset = pixelOffset;
	},

	visibleHeight: function() {
		return parseInt(this.div.style.height);
	}

});

//------------- Control.LiveGrid.Request
Control.LiveGrid.Request = Class.create({
	initialize: function(requestOffset, options) {
		this.requestOffset = requestOffset;
	}
});

//------------- Control.LiveGrid.Selector
Control.LiveGrid.Selector = Class.create({
	initialize: function(table, fetchHandler, metaData) {
		this.table = table;
		this.fetchHandler = fetchHandler;
		this.metaData = metaData;

		this.lastRowSelected = null;
		this.lastRangeSelected = null;

		this.rowIdPrefix = (metaData.options.rowIdPrefix ? metaData.options.rowIdPrefix : '');
		this.selectedClass = (metaData.options.selectedClass ? metaData.options.selectedClass : 'selected');
		this.onrowselect = metaData.options.onrowselect;
		this.onrowopen = metaData.options.onrowopen;

		// Set scrolling handler and initial offset
		this.currentOffset = metaData.options.offset ? metaData.options.offset : 0;
		metaData.options.onbeforescroll = this.handleScroll.bind(this);
		this.selections = Array();
		this.previousSelections = Array();
		this.applyRowBehavior();
	},
	applyRowBehavior: function() {
		// Setup row event handlers
		for(var i = 0; i < this.table.rows.length; ++i) {
			this.table.rows[i].onmousedown = this.rowmousedownhandler(i);
			this.table.rows[i].onmousemove = this.rowmousemovehandler(i);
			this.table.rows[i].onmouseup = this.rowmouseuphandler();
			this.table.rows[i].ondblclick = this.rowdblclickhandler();
			// IE text-selection fix
			this.table.rows[i].onselectstart = function() { return false; };
		}
	},
	/**
	 * Event handler factories.
	 */
	rowmousedownhandler: function(index) {
		return function(e) {
			this.dragging = true;
			this.onrowclick(index, e);
			if (this.onrowselect)
				this.onrowselect(e, this);
			// Cancel text selection in Moz
			Event.stop(e);
			return false;
		}.bindAsEventListener(this);
	},
	rowmousemovehandler: function(index) {
		return function(e) {
			if (this.dragging) {
				this.onrowclick(index, e, true);
				if (this.onrowselect)
					this.onrowselect(e, this);
			}
			return false;
		}.bindAsEventListener(this);
	},
	rowmouseuphandler: function(index) {
		return function(e) {
			this.dragging = false;
		}.bindAsEventListener(this);
	},
	rowdblclickhandler: function() {
		return function(e) {
			if (this.onrowopen)
				this.onrowopen(e, this);
			// Cancel text selection in Moz
			Event.stop(e);
		}.bindAsEventListener(this);
	},
	/**
	 * Event handlers to highlight table rows when clicked by
	 * setting the className to this.selectedClass.	Selecting ranges with
	 * CTL and SHIFT is also supported.
	 */
	onrowclick: function(index, e, dragged) {
		var rowId = this.table.rows[index].id;
		var rowNum = this.currentOffset + index;
		if (e.shiftKey || dragged) {
			// Save state for reversing range selection
			if (!this.previousSelections)
				this.previousSelections = this.copyArray(this.selections);
			// Restore state for reversing range selection
			else
				this.selections = this.copyArray(this.previousSelections);

			if (this.lastRowSelected < rowNum) {
				for (var i = this.lastRowSelected; i <= rowNum; ++i)
					this.selections[i] = this.table.rows[i - this.currentOffset].id;
			} else if (this.lastRowSelected > rowNum) {
				for (var i = this.lastRowSelected; i >= rowNum; --i)
					this.selections[i] = this.table.rows[i - this.currentOffset].id;
			}
			this.lastRangeSelected = rowNum;
		} else if (e.ctrlKey) {
			this.selections[rowNum] = this.selections[rowNum] ? null : rowId;
			this.lastRowSelected = rowNum;
			this.previousSelections = null;
		} else {
			this.deselectAllRows(true);
			this.selections[rowNum] = rowId;
			this.lastRowSelected = rowNum;
			this.previousSelections = null;
		}
		this.redrawSelections();
	},
	copyArray: function(ar) {
		var ret = new Array(ar.length);
		for (var i = 0; i < ar.length; ++i)
			ret[i] = ar[i];
		return ret;
	},
	/**
	 * Return the CSS ID of all rows marked by onrowclick() in the given table.
	 */
	selectedRows: function() {
		var selected = new Array();
		var offset = (this.rowIdPrefix ? this.rowIdPrefix.length : 0);
		for (var i = 0; i < this.selections.length; ++i) {
			if (this.selections[i])
				selected[selected.length] = this.selections[i].substring(offset);
		}
		return selected;
	},
	handleScroll: function(newOffset, pageSize, totalRows) {
		this.currentOffset = newOffset;
		this.redrawSelections();
	},
	selectAllRows: function() {
		// TODO: What do we do here?  Don't really want to load the whole dataset,
		// but can't really rely on something like a wildcard either.
		alert('Not implemented');
		if (this.onrowselect)
			this.onrowselect(null, this);
	},
	deselectAllRows: function(skipEvent) {
		this.selections = new Array();
		this.redrawSelections();
		this.lastRowSelected = null;
		this.previousSelections = null;
		if (this.onrowselect)
			this.onrowselect(null, this);
	},
	redrawSelections: function(offset) {
		offset = offset ? offset : this.currentOffset;
		for (var i = 0; i < this.table.rows.length; ++i) {
			if (offset + i < this.metaData.totalRows) {
				if (this.selections[offset + i])
					Element.addClassName(this.table.rows[i], this.selectedClass);
				else
					Element.removeClassName(this.table.rows[i], this.selectedClass);
			}
		}
	}
});

//-------- Control.LiveGrid.Sort
Control.LiveGrid.Sort = Class.create({
	initialize: function(table, metaData, sortHandler) {
		this.table = $(table);
		this.sortHandler = sortHandler;
		this.setOptions(metaData.options);
		this.columns = this.table.rows[0].cells;

		this.applySortBehavior(this.columns);
		this.initSortColumn();
	},
	initSortColumn: function() {
		var sortField = this.options.sortField;
		if (sortField) {
			var sortDirection = this.options.sortDirection ? this.options.sortDirection : 'asc';
			for (var i = 0; i < this.columns.length; ++i)
				if (this.columns[i].getAttribute('sortField') == sortField)
					this.setSortColumn(this.columns[i], sortDirection);
		}
	},
	setOptions: function(options) {
		var base = Protoplasm.base('livegrid');
		var defaults = {
			sortAscendImg: base+'sort_asc.png',
			sortDescendImg: base+'sort_desc.png',
			imageWidth: 9,
			imageHeight: 5};
		this.options = Object.extend(defaults, options);

		// preload the images...
		new Image().src = this.options.sortAscendImg;
		new Image().src = this.options.sortDescendImg;
	},
	applySortBehavior: function(cells) {
		for (var i = 0; i < cells.length; ++i) {
			if (this.isSortable(i)) {
				var cellName = this.options.sortFields ? this.options.sortFields[i] : cells[i].id;
				cells[i].setAttribute('sortField', cellName);
				cells[i].style.cursor = 'pointer';
				cells[i].onclick = this.onclick.bindAsEventListener(this);
				cells[i].innerHTML += '<span id="' + cellName + '_img">' + '&nbsp;&nbsp;&nbsp;</span>';
			}
		}
	},
	isSortable: function(column) {
		return (!this.options.sortFields || this.options.sortFields[column])
	},
	onclick: function(e) {
		var cell = Event.element(e);
		// Find real cell when click is fired by children
		while (cell.tagName.toUpperCase() != 'TD' && cell.tagName.toUpperCase() != 'TH')
			cell = cell.parentNode;
		this.setSortColumn(cell);
		this.executeSort();
	},
	setSortColumn: function(cell, direction) {
		if (cell.getAttribute('sortField') == this.sortField) {
			this.sortDirection = (this.sortDirection == 'asc' ? 'desc' : 'asc');
		} else {
			this.sortField = cell.getAttribute('sortField');
			this.sortDirection = 'asc';
		}
		this.refreshColumnDisplay();
	},
	refreshColumnDisplay: function() {
		for (var i = 0; i < this.columns.length; ++i) {
			if (this.columns[i].onclick) {
				var image = $(this.columns[i].getAttribute('sortField') + '_img');
				if (this.columns[i].getAttribute('sortField') == this.sortField) {
					if (this.sortDirection == 'asc') {
						image.innerHTML = '&nbsp;&nbsp;<img width="'  + this.options.imageWidth    + '" ' +
							'height="'+ this.options.imageHeight   + '" ' +
							'src="'   + this.options.sortAscendImg + '"/>';
					} else if (this.sortDirection == 'desc') {
						image.innerHTML = '&nbsp;&nbsp;<img width="'  + this.options.imageWidth    + '" ' +
							'height="'+ this.options.imageHeight   + '" ' +
							'src="'   + this.options.sortDescendImg + '"/>';
					} else {
						image.innerHTML = '&nbsp;&nbsp;';
					}
				} else {
					image.innerHTML = '&nbsp;&nbsp;';
				}
			}
		}
	},
	executeSort: function() {
		this.sortHandler(this.sortField, this.sortDirection);
	}
});

Protoplasm.register('livegrid', Control.LiveGrid);
