// LessWrong anti-kibitzer version 0.5
// Originally authored by Marcello Herreshoff
// Versions 0.44 and further by Morendil
// Allows the user to toggle whether point values and commenters are shown on LW.

var kib_hidden = true;

function toggle_kibitzing(){
  kbutton = document.getElementById("kbutton")
  if(kib_hidden){
    kib_hidden = false;
    kbutton.value = "Turn Kibitzing Off";
  }else{
    kib_hidden = true;
    kbutton.value = "Turn Kibitzing On";
  }
  apply_kibitzing()
}

function apply_kibitzing(){
  function ak_hide(n) { n.style.display = "none"; }
  function ak_show(n) { n.style.display = "inline"; }

  // locate the AK stylesheet
  var css;
  for (var i=0; i < document.styleSheets.length; i++) {
    if (document.styleSheets[i].href.indexOf("antikibitzer") > 0)
      css = document.styleSheets[i];
  }

  var rules = css.cssRules;
  if (!rules) rules = css.rules; // IE compatibility

  var nbRules = rules.length;
  for (var i=0; i < nbRules; i++) {
    var rule = rules[i];
    if (kib_hidden) ak_hide(rule); else ak_show(rule);
  }
}

var div = document.createElement("div");
var pos = "fixed";
if (document.styleSheets[1].rules) pos = "absolute"; // IE compatibility
div.innerHTML = "<div id='kfloat' style='position:"+pos+";top:0px;right:0px'><form><input id='kbutton' type='button' value='Turn Kibitzing On' onclick='toggle_kibitzing()'/></form>";

document.body.appendChild(div);
