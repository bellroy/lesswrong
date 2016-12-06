/**
 * This JavaScript adds a "min-width" attribute to the viewport meta tag. If
 * the device's width is less than the min-width, we will scale the viewport
 * to the min-width; otherwise we will leave the meta tag alone.
 *
 * This script must be added *after* the viewport meta tag, since it relies on
 * that tag already being available in the DOM.
 *
 * Implementation note: The reason we remove the old tag and insert a new one
 *                      is that Firefox doesn't pick up changes to the viewport
 *                      meta tag.
 *
 * Author: Brendan Long <self@brendanlong.com>
 * License: Public Domain - http://unlicense.org/
 * See: https://github.com/brendanlong/viewport-min-width-polyfill
 */
(function() {
  var viewport = document.querySelector("meta[name=viewport]");
  if (viewport) {
    var content = viewport.getAttribute("content");
    var parts = content.split(",");
    for (var i = 0; i < parts.length; ++i) {
      var part = parts[i].trim();
      var pair = part.split("=");
      if (pair[0] === "min-width") {
        var minWidth = parseInt(pair[1]);
        if (screen.width < minWidth) {
          document.head.removeChild(viewport);

          var newViewport = document.createElement("meta");
          newViewport.setAttribute("name", "viewport");
          newViewport.setAttribute("content", "width=" + minWidth);
          document.head.appendChild(newViewport);
          break;
        }
      }
    }
  }
})();

