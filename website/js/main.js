const VERBOSE = true;
const TIMEOUT = 5000; // in ms
const DEFAULT_API_HOSTNAME = "http://localhost";

function ApiRequest(command=""){
  var postValues = {};
  var command = command;

  /*
  Due to the ascynhronous nature of javascript and these types of requests, a function
  must be defined to be called upon the response of the API. This can be set
  after a new object is instantated and so it can be done on a case by
  case basis.
  */

  var calledOnResponse = function(response){
    alert(response.status.code.toString() + ": " + response.status.text);
  };

  this.setCalledOnResponse = function(func){
    calledOnResponse = func;
  };

  this.setCommand = function(command){
    this.command = command;
  };

  this.addContent = function(content, parameter){
      postValues[parameter] = content;
  };

  this.send = function(){
    var req = new XMLHttpRequest();

    /*
    The next line waits (but lets the code carry on much like a new thread)
    for the time TIMEOUT then checks if the request has been completed sucessfully,
    if not it alerts the user accordingly because the right hostname for the API
    problably hasn't been set.
    */

    setTimeout(
      function(){
        if (req.readyState != 4){
          alert("Sorry, there was a problem connecting to the controller server, check the hostname is correct.")
          console.log("Server connection issue. Perhaps check that the server hostname is set correctly.")
        };
      }, TIMEOUT
    );

    var url = getCookie("ApiHostname") + "/" + command;

    req.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200){ // if the request is done and was successful
        console.log(this.resonseText);
        calledOnResponse(JSON.parse(this.responseText));
      }

      else if(this.readyState == 4 && this.status != 200){ // if the request is done and not successful
        alert("There was a problem with the API; contact help.");
        console.log("API Connection Problem: Error " + this.status.toString());
      };
    };

    req.open("POST", url, true);
    req.setRequestHeader("Content-Type", "application/json"); // this header must be set to let the flask API know it's getting JSON

    if (VERBOSE){
      console.log("ApiRequest sent to " + command);
      console.log("With POST values " + JSON.stringify(postValues));
    }

    req.send(JSON.stringify(postValues));
  }
}

function getCookie(cookieName){
  var cookieData = document.cookie;

  /*
  There's no function to get a single cookie,
  instead you have to write one to parse a string of ; seperated
  cookies yourself.
  */

  if (VERBOSE){
    console.log("Cookies: " + cookieData);
  }

  var cookiePairs = cookieData.split("; ");

  var cookies = {};

  for (i = 0; i < cookiePairs.length; i++){
    var pair = cookiePairs[i].split("=");

    cookies[pair[0]] = pair[1];
  }

  return cookies[cookieName];
}

function getGETParameter(parameter){
 var getData = window.location.search.substr(1)

 var getPairs = getData.split("&");

 var gets = {};

 for (i = 0; i < getPairs.length; i++){
   var pair = getPairs[i].split("=");

   gets[pair[0]] = pair[1];
  }

  return gets[parameter];
}

function deleteCookie(cookie){
  /*
  Sets expiry date in the past and the browser takes care of it, no other way to do it...
  */

  document.cookie = cookie + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}

function goToLoginIfSessionKeyNotValid(){
  var sessionKey = getCookie("sessionKey");

  if (! sessionKey){
    document.location.href = "/login.html";
    return
  };

  var req = new ApiRequest("is_session_key_valid");

  req.setCalledOnResponse(
    function(response){
      if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
        return
      };

      if (response.is_valid == "false"){
        document.location.href = "/login.html";
        return
      }
      else {
        console.log("Session key okay!");
        return
      };
    }
  );

  req.addContent(sessionKey, "session_key");

  req.send()
}

function log_out(){
  var req = new ApiRequest("log_out");

  req.setCalledOnResponse(
    function(response){
      if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
        return
      }

      else {
        deleteCookie("sessionKey");
        document.location.href = "/login.html";
        return
      };
    }
  );

  var sessionKey = getCookie("sessionKey");
  req.addContent(sessionKey, "session_key")

  req.send();
}

function setApiHostname(hostname){
  var currentDate = new Date();
  currentDate.setTime(currentDate.getTime() + (30*365*24*60*60*1000)); // 30 years exipry date, no other way to make no exipry cookie...
  document.cookie = "ApiHostname=" + hostname + "; expires=" + currentDate.toGMTString() + "; path=/";
}

function setApiHostnameAsDefaultIfNotSet(){
  var hostname = getCookie("ApiHostname");

  if (! hostname){
    setApiHostname(DEFAULT_API_HOSTNAME);
  };
}

function closeHostnameSetter(){
  var menu = document.getElementById("hostnameMenu");
  menu.parentNode.removeChild(menu);
}

function openHostnameSetter(){
  if (document.getElementById("hostnameMenu") != undefined){
    return;
  };

  var hostnameDiv = document.createElement("div");
  hostnameDiv.className = "hostname_setter_container";
  hostnameDiv.setAttribute("id", "hostnameMenu");

  var instructionsDiv = document.createElement("div");
  instructionsDiv.className = "hostname_setter_label";
  var tempTextNode = document.createTextNode("The current hostname is displayed below, press the exit button to leave as is, or enter a new one and press apply to set a new one. (Must include http:// etc)");
  instructionsDiv.appendChild(tempTextNode);

  var exitButtonDiv = document.createElement("button");
  exitButtonDiv.className = "normal_button hostname_setter_exit";
  exitButtonDiv.setAttribute("onclick", "closeHostnameSetter()");
  var tempTextNode = document.createTextNode("X");
  exitButtonDiv.appendChild(tempTextNode);

  var hostnameEntry = document.createElement("input");
  hostnameEntry.className = "normal_text_entry hostname_setter_text_entry";
  hostnameEntry.setAttribute("id", "new_hostname");
  hostnameEntry.setAttribute("type", "text");
  hostnameEntry.setAttribute("value", getCookie("ApiHostname"));

  var applyButton = document.createElement("button");
  applyButton.className = "normal_button hostname_setter_apply";
  applyButton.setAttribute("onclick", "setApiHostname(document.getElementById('new_hostname').value);closeHostnameSetter();");
  var tempTextNode = document.createTextNode("Apply");
  applyButton.appendChild(tempTextNode);

  elementsToAdd = [instructionsDiv, exitButtonDiv, hostnameEntry, applyButton];

  for (i = 0; i < elementsToAdd.length; i++){
    hostnameDiv.appendChild(elementsToAdd[i]);
  };

  document.body.appendChild(hostnameDiv);
}

function randomChoice(array){
  var randomIndex = Math.floor(Math.random() * array.length);
  return array[randomIndex]
}

function removeElementByAttributeAndValue(attribute, value){
  document.querySelectorAll("[" + attribute + "=" + value + "]")[0].parentElement.removeChild(document.querySelectorAll("[" + attribute + "=" + value + "]")[0]);
}
