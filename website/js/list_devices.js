const DEVICE_REFRESH_RATE = 5 // in seconds

function addDeviceToPage(device){
  var deviceElement = document.createElement("div");  // creating the main div container for the device
  deviceElement.className = "device_description_container";
  deviceElement.setAttribute("deviceID", device.id);

  // purely asthetic random border colour setting below

  deviceElement.setAttribute("style", "border-color: " + randomChoice(["#FF8987", "#728AFF", "#7FFFA1"]));

  var subElements = { // elements to put in the device container
    name: {
      elementType: "div",
      content: device.name,
      label: "",
      className: "device_name"
    },

    owner: {
      elementType: "div",
      content: device.owner,
      label: "Owned by ",
      className: "owner_username"
    },

    type: {
      elementType: "div",
      content: device.type,
      label: "Type: ",
      className: "device_type"
    },

    button: {
      elementType: "button",
      content: "More",
      label: "",
      className: "normal_button device_button"
    }
  };

  if (VERBOSE){
    console.log("Device added:");
  };

  for (element in subElements){
    subElements[element].element = document.createElement(subElements[element].elementType);
    subElements[element].element.className = subElements[element].className;

    var elementText = subElements[element].label + subElements[element].content;
    var tempTextNode = document.createTextNode(elementText);
    subElements[element].element.appendChild(tempTextNode);

    deviceElement.appendChild(subElements[element].element);

    if (VERBOSE){
      console.log(element + ": " + subElements[element].content);
    };
  };

  subElements.button.element.setAttribute("onclick", "goToDevicePage(this);");

  document.getElementsByClassName("centered_container")[0].appendChild(deviceElement);
};

function updateListedDevices(){
  req = new ApiRequest("list_devices");

  req.setCalledOnResponse(
    function(response){
      var deviceElements = document.getElementsByClassName("device_description_container");

      /*
      The code below removes all elements of class name "device_description_container". It works
      and is acceptable because when document.getElements<etc> is called, a static array is not returned
      instead a "live" iterable object is returned and so when an element is removed from the actual document
      it is removed from the "list".
      */

      while(deviceElements[0]){
        deviceElements[0].parentNode.removeChild(deviceElements[0]);
      };

      for (device in response.devices){
        addDeviceToPage(response.devices[device]);
      };
        
      var refreshButton = document.getElementsByClassName("normal_button refresh_button")[0];
      refreshButton.innerHTML = "Refresh Devices";
    }
  );

  req.addContent(getCookie("sessionKey"), "session_key");

  var refreshButton = document.getElementsByClassName("normal_button refresh_button")[0];
  if (refreshButton != undefined){
    refreshButton.innerHTML = "Talking to API...";
  };

  req.send();
}

function goToDevicePage(buttonElement){ // function for the "more" button to send the clicker to the device page of the container
  document.location.href = '/device.html?deviceID=' + buttonElement.parentNode.getAttribute('deviceID');
}
