function refreshTemperature(deviceID){
  req = new ApiRequest("call_command_on_device");

  req.setCalledOnResponse(
    function (response){
      if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
        return;
      };

      console.log("Updated device temp!")
      console.log(response.device_response)
      var statusElement = document.getElementsByClassName("current_temp")[0]
      statusElement.innerHTML = response.device_response.temperature.toString()
    }
  );

  req.addContent(getCookie("sessionKey"), "session_key");
  req.addContent(getGETParameter("deviceID"), "device_id");
  req.addContent("gtm", "command_code");

  var temperatureElement = document.getElementsByClassName("current_temp")[0]
  temperatureElement.innerHTML = "Finding"

  req.send();
}

function applyPermission(){
  /*
  This function gathers up all of the permission data from the page
  and sends it over to the API to set as the new permission for this device.
  */

  req = new ApiRequest("set_device_permission");

  var applyButton = document.getElementsByClassName("normal_button apply_permission")[0];
  applyButton.innerHTML = "Applying..."

  req.setCalledOnResponse(
    function (response){
      if (response.status.code != 1){
        alert("Error applying permission, code " + response.status.code.toString() + ": " + response.status.text)
        return;
      };

      var applyButton = document.getElementsByClassName("normal_button apply_permission")[0];
      applyButton.innerHTML = "Apply Permission"
      updatePermission();
    }
  );

  var permissionDropdown = document.getElementById("permission_types_dropdown");
  var permissionType = permissionDropdown.options[permissionDropdown.selectedIndex].text;

  var userContainerElementHTMLCollection = document.getElementsByClassName("permission_username");
  var userContainersElementArray = Array.prototype.slice.call(userContainerElementHTMLCollection);
  var usernamesToBeAdded = userContainersElementArray.map(function(element){return element.innerHTML});

  if (VERBOSE){
    console.log("To be added: ")
    console.log(usernamesToBeAdded)
  }

  req.addContent(usernamesToBeAdded, "users");
  req.addContent(permissionType, "permission_type");
  req.addContent(getCookie("sessionKey"), "session_key");
  req.addContent(getGETParameter("deviceID"), "device_id");
  req.send();
}

function addSelectedUserToPermission(){
  var userDropdown = document.getElementById("users_dropdown");
  var username = userDropdown.options[userDropdown.selectedIndex].text;

  var userContainers = document.querySelectorAll("[user_in_permission=" + username + "]");
  console.log(userContainers);
  if (userContainers.length > 0){
    return;
  };

  addUser(username);
}

function addUser(username){
  // Creates a user container on the page with the username supplied.

  var permissionsBox = document.getElementById("permissions_box");

  var userContainer = document.createElement("div");
  userContainer.className = "permission_user_container";
  userContainer.setAttribute("user_in_permission", username);

  var usernameLabel = document.createElement("div");
  usernameLabel.className = "permission_username";
  var tempTextNode = document.createTextNode(username);
  usernameLabel.appendChild(tempTextNode);

  var removalButton = document.createElement("button");
  var tempTextNode = document.createTextNode("Remove");
  removalButton.appendChild(tempTextNode);
  removalButton.className = "normal_button remove_user_from_permission";
  removalButton.setAttribute("onclick", "removeElementByAttributeAndValue('" + "user_in_permission" + "', '" + username + "')");

  userContainer.appendChild(removalButton);
  userContainer.appendChild(usernameLabel);

  permissionsBox.appendChild(userContainer);
}

function updatePermission(){
  // Request for list of device types and set them in the dropdown options menu

  req = new ApiRequest("get_permission_types");

  req.setCalledOnResponse(
    function (response){
      if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
        return;
      };

      var dropdownElement = document.getElementById("permission_types_dropdown");
      dropdownElement.innerHTML = "";

      for (type in response.types){
        var tempElement = document.createElement("option");
        tempElement.setAttribute("id", response.types[type].name)
        var tempTextNode = document.createTextNode(response.types[type].name);
        tempElement.appendChild(tempTextNode);
        dropdownElement.appendChild(tempElement);
      };
    }
  );

  req.send();

  // Request for list of users and then set them as options in the dropdown options menu

  req = new ApiRequest("get_users_list");

  req.setCalledOnResponse(
    function (response){
      if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
        return;
      };

      var dropdownElement = document.getElementById("users_dropdown");
      dropdownElement.innerHTML = "";

      for (user in response.users){
        var tempElement = document.createElement("option");
        var tempTextNode = document.createTextNode(response.users[user]);
        tempElement.appendChild(tempTextNode);
        dropdownElement.appendChild(tempElement);
      };
    }
  );

  req.send()

  // Gets the users related to the current device permission and the permission type and adds them to the page

  req = new ApiRequest("get_device_permission_info");

  req.setCalledOnResponse(
    function (response){
      if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
        return;
      };

      var permissionTypesDropdown = document.getElementById("permission_types_dropdown");
      var indexOfPermissionType = Array.prototype.slice.call(permissionTypesDropdown.options).indexOf(document.getElementById(response.permission.type))
      permissionTypesDropdown.selectedIndex = indexOfPermissionType;

      var currentUserElements = document.getElementsByClassName("permission_user_container");

      while (currentUserElements[0]){
        currentUserElements[0].parentNode.removeChild(currentUserElements[0]);
      };

      console.log(response.permission);

      for (user in response.permission.users){
        addUser(response.permission.users[user]);
      };
    }
  );

  req.addContent(getCookie("sessionKey"), "session_key");
  req.addContent(getGETParameter("deviceID"), "device_id");
  req.send();
}

function buildDevicePermissions(device){
  // Creating the permissions box
  var permissionsBox = document.createElement("div");
  permissionsBox.className = "permissions_box";
  permissionsBox.setAttribute("id", "permissions_box");

  // Elements to put in the toggle box.
  var subElements = {
    title: {
      elementType: "div",
      content: "Device Permission",
      className: "permissions_title"
    },

    applyButton: {
      elementType: "button",
      content: "Apply Permission",
      className: "normal_button apply_permission"
    },

    description: {
      elementType: "div",
      content: "The info below shows the type of permission on the device I.E. blacklist, whitelist etc. The users shown below the add user field (if there are any) are ones relating to the permission hence we use a blacklist, they will be blacklisted and the same for a whitelist. If using a permission type where having users related to it is irrellevant, they are simply ignored.",
      className: "permission_explaination"
    }
  };

  for (element in subElements){
    subElements[element].element = document.createElement(subElements[element].elementType);
    subElements[element].element.className = subElements[element].className;

    var tempTextNode = document.createTextNode(subElements[element].content);
    subElements[element].element.appendChild(tempTextNode);

    permissionsBox.appendChild(subElements[element].element);

    if (VERBOSE){
      console.log(element + ": " + subElements[element].content);
    };
  };

  subElements.applyButton.element.setAttribute("onClick", "applyPermission()");

  document.getElementsByClassName("centered_container")[0].appendChild(permissionsBox);

  // Making the Permission Type selector

  var permissionTypes = document.createElement("div");
  permissionTypes.className = "permission_header_container";

  var permissionTypesLabel = document.createElement("div");
  permissionTypesLabel.className = "permission_types_label";
  var tempTextNode = document.createTextNode("Permission Type: ");
  permissionTypesLabel.appendChild(tempTextNode);
  permissionTypes.appendChild(permissionTypesLabel);

  var permissionsDropdown = document.createElement("select");
  permissionsDropdown.className = "permissions_dropdown";
  permissionsDropdown.setAttribute("id", "permission_types_dropdown");
  permissionTypes.appendChild(permissionsDropdown);

  permissionsBox.appendChild(permissionTypes);

  // Making the User Adder

  var userSelect = document.createElement("div");
  userSelect.className = "permission_header_container";

  var userSelectLabel = document.createElement("div");
  userSelectLabel.className = "user_select_label";
  var tempTextNode = document.createTextNode("Add User: ");
  userSelectLabel.appendChild(tempTextNode);
  userSelect.appendChild(userSelectLabel);

  var userSelectDropdown = document.createElement("select");
  userSelectDropdown.className = "permissions_dropdown user_select";
  userSelectDropdown.setAttribute("id", "users_dropdown");
  userSelect.appendChild(userSelectDropdown);

  var addUserButton = document.createElement("button");
  addUserButton.className = "normal_button add_user_to_permission";
  var tempTextNode = document.createTextNode("Add");
  addUserButton.appendChild(tempTextNode);
  addUserButton.setAttribute("onClick", "addSelectedUserToPermission()");
  userSelect.appendChild(addUserButton);

  permissionsBox.appendChild(userSelect);

  // Function below updates the options with fresh data from the controller server

  updatePermission();
}

function updateStatus(){
  req = new ApiRequest("call_command_on_device");

  req.setCalledOnResponse(
    function (response){
      if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
        return;
      };

      console.log("Updated device state!")
      console.log(response.device_response)
      var statusElement = document.getElementsByClassName("current_state")[0]
      statusElement.innerHTML = (response.device_response.state == "0") ? "Current State: Off" : "Current State: On"
    }
  );

  req.addContent(getCookie("sessionKey"), "session_key");
  req.addContent(getGETParameter("deviceID"), "device_id");
  req.addContent("gcs", "command_code");

  var statusElement = document.getElementsByClassName("current_state")[0]
  statusElement.innerHTML = "Querying status..."

  req.send();
}

function toggleDevice(){
  req = new ApiRequest("call_command_on_device");

  req.setCalledOnResponse(
    function (response){
      if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
        return;
      };

      updateStatus(getGETParameter("deviceID"));
    }
  );

  req.addContent(getCookie("sessionKey"), "session_key");
  req.addContent(getGETParameter("deviceID"), "device_id");
  req.addContent("tgl", "command_code");

  var statusElement = document.getElementsByClassName("current_state")[0]
  statusElement.innerHTML = "Talking to device..."

  req.send();
}

function buildPage(device){
  // Creates a device title at the top of page.
  var deviceTitle = document.createElement("div");
  deviceTitle.className = "big_title";
  var tempTextNode = document.createTextNode(device.name);
  deviceTitle.appendChild(tempTextNode);
  document.getElementsByClassName("centered_container")[0].appendChild(deviceTitle);


  // If the device is a switch, a toggle box is made.
  if (device.type == "Switch"){
    // Creating the main div container for the toggle box.
    var toggleBox = document.createElement("div");
    toggleBox.className = "toggle_box";

    // Elements to put in the toggle box.
    var subElements = {
      toggle: {
        elementType: "button",
        content: "Toggle",
        className: "normal_button toggle_button"
      },

      state: {
        elementType: "div",
        content: "Querying State...",
        className: "current_state"
      },

      owner_and_type: {
        elementType: "div",
        content: device.type + " owned by " + device.owner,
        className: "owner_and_type"
      }
    };

    if (VERBOSE){
      console.log("Toggle Box added:");
    };

    for (element in subElements){
      subElements[element].element = document.createElement(subElements[element].elementType);
      subElements[element].element.className = subElements[element].className;

      var tempTextNode = document.createTextNode(subElements[element].content);
      subElements[element].element.appendChild(tempTextNode);

      toggleBox.appendChild(subElements[element].element);

      if (VERBOSE){
        console.log(element + ": " + subElements[element].content);
      };
    };

    subElements.toggle.element.setAttribute("onClick", "toggleDevice('" + device.id.toString() + "')");

    document.getElementsByClassName("centered_container")[0].appendChild(toggleBox);

    updateStatus(device.id.toString())
  }
  
  else{
    // Creating the main div container for the thermometer box.
    var thermometerBox = document.createElement("div");
    thermometerBox.className = "thermometer_box";

    // Elements to put in the thermometer box.
    var subElements = {
      button: {
        elementType: "button",
        content: "Refesh Reading",
        className: "normal_button toggle_button"
      },

      temperature: {
        elementType: "div",
        content: "Querying Temp...",
        className: "current_temp"
      },

      owner_and_type: {
        elementType: "div",
        content: device.type + " owned by " + device.owner,
        className: "owner_and_type"
      }
    };

    if (VERBOSE){
      console.log("Thermometer Box added:");
    };

    for (element in subElements){
      subElements[element].element = document.createElement(subElements[element].elementType);
      subElements[element].element.className = subElements[element].className;

      var tempTextNode = document.createTextNode(subElements[element].content);
      subElements[element].element.appendChild(tempTextNode);

      thermometerBox.appendChild(subElements[element].element);

      if (VERBOSE){
        console.log(element + ": " + subElements[element].content);
      };
    };

    subElements.button.element.setAttribute("onClick", "refreshTemperature('" + device.id.toString() + "')");

    document.getElementsByClassName("centered_container")[0].appendChild(thermometerBox);

    refreshTemperature(device.id.toString())
  };

  buildDevicePermissions();
}

function loadDeviceInfo(){
  req = new ApiRequest("get_device_info");

  req.setCalledOnResponse(
    function(response){
      if (response.status.code == 9){
        alert("Sorry, you don't have permission to view this device.");
        window.location.href = "/list_devices.html";
        return;
      }

      else if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
      }

      else {
        buildPage(response.device);
      };
	  }
  );

  req.addContent(getCookie("sessionKey"), "session_key");
  req.addContent(getGETParameter("deviceID"), "device_id")

  req.send();
}
