// ==UserScript==
// @name           LessWrong anti-kibitzer
// @namespace      http://stanford.edu/~marce110/
// @description    Allows the user to toggle whether point values and commenters are shown on LW.
// @include        http://*lesswrong.com/*
// @include        http://*.lesswrong.com/*
// ==/UserScript==


// LessWrong anti-kibitzer version 0.45
// Thanks to Baughn for fixing the flickering bug.

function forallElts(pattern, fn){
  var allElts = document.evaluate(pattern,
      document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
  for(var i = 0 ; i < allElts.snapshotLength ; i++){
    fn(allElts.snapshotItem(i));
  }
}

function forallKibitzes(fn){
  forallElts("//span[contains(@class,'author')]", fn)
  forallElts("//span[contains(@class,'score')]", fn)
  forallElts("//span[contains(@class,'votes')]", fn)
  forallElts("//span[contains(@id,'score')]", fn)
  forallElts("//div[contains(@class,'reddit-link')]//span", fn)
  forallElts("//div[@id='siteTable']//a[contains(@href,'lesswrong.com/user')]", fn)
  forallElts("//div[@id='side-comments']//a[contains(@href,'lesswrong.com/user')]", fn)
}

function ak_hide(n) { n.style.display = "none"; }
function ak_show(n) { n.style.display = "inline"; }

var kib_hidden = true;
function toggle_kibitzing(){
  kbutton = document.getElementById("kbutton")
  if(kib_hidden){
    kib_hidden = false;
    kbutton.value = "Turn Kibitzing On";
  }else{
    kib_hidden = true;
    kbutton.value = "Turn Kibitzing Off";
  }
  apply_kibitzing()
}

function apply_kibitzing(){
  if (kib_hidden)
    forallKibitzes(ak_show);
  else
    forallKibitzes(ak_hide);
}

apply_kibitzing();

var div = document.createElement("div")
div.innerHTML = "<div id='kfloat' style='position:fixed;top:0px;right:0px'><form><input id='kbutton' type='button' value='Turn Kibitzing On' onclick='toggle_kibitzing()'/></form></div><script>toggle_kibitzing()</script>";

document.body.appendChild(div);

Ajax.Responders.register({
  onComplete: function(request,response,json) {
    if ((request.url == "/api/side_comments") || (request.url == "/api/side_posts"))
	apply_kibitzing();
  }
});
