function init_tinymce() {
  tinyMCE.init({
    mode : "exact",
    elements : "article",
    theme : "advanced",
    width : "100%",
    content_css : "/static/reddit.css",
    body_class : "md",
    theme_advanced_toolbar_location : "top",
    theme_advanced_buttons1 : "formatselect,|,bold,italic,underline,strikethrough,blockquote,summarybreak,|,bullist,numlist,|,outdent,indent,|,link,unlink,anchor,image,code,html,|,hr,removeformat,|,sub,sup,|,charmap",
    theme_advanced_buttons2 : "",
    theme_advanced_buttons3 : "",
    plugins : "summarybreak,advimage", //inlinepopups,
    file_browser_callback : 'showImageBrowser'
  }); 
};

function showImageBrowser(field_name, url, type, win) {
  var location = window.location;
  
  // Get the last path component
  var path = location.pathname;
  var article_id = '';
  if(matches = path.match(/\/([^\/]+)$/)) {
    article_id = matches[1];
  }

  tinyMCE.activeEditor.windowManager.open({
      file : location.protocol + '//' + location.host + '/imagebrowser/' + article_id,
      title : 'Image Browser',
      width : 640,
      height : 400,
      resizable : "yes",
      scrollable : "yes",
      inline : "yes",  // Requires inlinepopups plugin to have affect
      close_previous : "no"
  }, {
      window : win,
      input : field_name
  });
  return false;
};
