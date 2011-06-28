(function ($) {

  window.featuredArticles = function(div,num) {
    if (!div)
      return;
    var t = $(div).attr("data-start-date");
    if (t)
      t = (new Date(t)).getTime();
    else
      t = (new Date()).getTime();

    var millisInWeek = 1000*86400*7;
    var weekNum = Math.floor(((new Date()).getTime() - t)/millisInWeek);
    if (weekNum<0) weekNum = -weekNum;

    var res = new Array();
    var items = $('li',div);
    for (i=0; i<num; i++) {
      var li = items[ (num*weekNum+i)%items.length ];
      res.push( li.innerHTML.trim() );
    }
    return res;
  };

})(jQuery);
