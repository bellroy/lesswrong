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
    plugins : "summarybreak",
  }); 
};