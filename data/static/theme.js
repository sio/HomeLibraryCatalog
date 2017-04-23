/* CONSTANTS */
var AJAX_URL = "/ajax";
var INVALID_CLASSNAME = "invalid";
var ajaxSuggestions = new AjaxHandler(ajaxFillSuggestions);


function encodeQueryData(data) {
    /**
    Encode get parameters for URL
    
    http://stackoverflow.com/a/111545
    **/
    var ret = [];
    var d
    for (d in data) {
        ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]));
    }
    return ret.join('&');
}


function AjaxHandler(callback) {
    /**
    Ajax object constructor
    
    Properties:
        xhr
            XMLHttpRequest object
        callback
            A function to be called upon server response. Xhr
            is passed to callback function as the first argument
        delay
            Integer. Minimum time between requests in milliseconds
        
    Methods:
        get(url)
            Perform AJAX request to url. Honors `delay` property
        getNow(url)
            The same as `get` but without mandatory delay
    **/
    var self = this;

    this.xhr = new XMLHttpRequest();
    this.timer = 0;
    this.delay = 300;
    this.callback = callback;
    this.xhr.onreadystatechange = function() {
        if (self.xhr.readyState === 4 && self.xhr.status === 200) { 
            self.callback(self.xhr);
        };
    };
    this.get = function(url) {
        clearTimeout(self.timer);
        self.timer = setTimeout(function() {self.getNow(url);}, self.delay);
    };
    this.getNow = function(url) {
        self.xhr.open("GET", url, true);
        self.xhr.send();
    };
};


function ajaxGetSuggestions(input) {
    /**
    Get suggestions for input field via AJAX call
    **/
    if (input.value.length > 2) {
        var url="/ajax/suggest";
        var params = {"f": input.name, "q": input.value};
        input.setAttribute("list", input.name + "_suggestions");
        ajaxSuggestions.get(url + "?" + encodeQueryData(params));
    };
};


function ajaxFillSuggestions(xhr) {
    /**
    Fill datalist with input suggestions
    Callback function for AjaxHandler object
    **/
    var result = JSON.parse(xhr.responseText);
    var field
    for (field in result) {
        if (result[field].length > 0) {
            var input = document.querySelector('input[name="' + field + '"]');
            var datalist = getDatalist(input);
            if (datalist) {
                removeChildNodes(datalist);
                var line;
                for (line in result[field]) {
                    var opt = document.createElement("option");
                    opt.value = result[field][line];
                    datalist.appendChild(opt);
                };
            };
        };
    };
};


function getDatalist(input) {
    /**
    Return datalist corresponding to input object
    Create new datalist object if necessary
    
    Return null if input object has no `list` attribute
    **/
    var datalist = input.list; // try getting the object directly
    if (!datalist) { // create datalist object if not exists
        var datalistID;
        datalistID = input.getAttribute("list");
        if (datalistID) {
            datalist = document.createElement("datalist");
            datalist.id = datalistID;
            input.parentNode.insertBefore(datalist, input);
        };
    };
    return datalist;
};


function removeChildNodes(node) {
    /**
    Remove all children nodes
    **/
    while (node.lastChild) {
        node.removeChild(node.lastChild);
    };
};




function cloneAuthor(node) {
    var newAuthor;
    cloneParent(node);
    newAuthor = node.parentNode.nextSibling.firstChild;
    newAuthor.value = "";
    newAuthor.focus();
    return false;
};

function cloneParent(node) {
    var original;
    var copy;
    var container;
    original = node.parentNode;
    copy = original.cloneNode(true);
    container = original.parentNode;
    if (container.lastChild === original) {
        container.appendChild(copy);
    } else {
        container.insertBefore(copy, original.nextSibling);
    };
    return false;
};

function checkDefaultValue(field) {
    trimField(field);
    if (field.value === field.defaultValue) {field.value = ""};
};

function checkDateField(field) {
    /**
    Validate the field that has to contain date value in DD.MM.YYYY format
    **/
    var valid;
    var date_array;
    var day;
    var month;
    var year;
    var days_in_month;
    var delimiter;

    trimField(field);

    delimiter = field.value.replace(/\d/g, "")[0]; //first non-numeric character
    date_array = field.value.split(delimiter);
    if (date_array.length===3) {
        day = Number(date_array[0]);
        month = Number(date_array[1]);
        year = Number(date_array[2]);
        valid = (year>=1900) && (year<=2100);
        valid = valid && (month>0) && (month<=12);
        days_in_month = new Date(year, month, 0).getDate();
        valid = valid && (day>0) && (day<=days_in_month);
    } else {
        valid = false;
    };

    if (field.value.length === 0) {
        valid = true;
    };

    showFieldValidation(field, valid);
};

function trimField(field) {
    field.value = field.value.replace(/^\s+|\s+$/g,""); //trim()
};

function checkYearField(field) {
    var year;
    var valid;
    trimField(field);
    year = parseInt(field.value);
    if (isNaN(year)) {
        year = "";
    };
    field.value = year;
    valid = and(year>=1900, year<=2100);

    if (field.value.length === 0) {
        valid = true;
    };

    showFieldValidation(field, valid);
};

function checkPriceField(field) {
    /**
    Validate price field. Empty values are allowed
    **/
    var price;
    var valid;
    trimField(field);
    price = parseFloat(field.value);
    if (isNaN(price)) {
        price = ""
    };
    field.value = price;
    valid = price > 0;

    if (field.value.length === 0) {
        valid = true;
    };

    showFieldValidation(field, valid);
};

function checkRequiredField(field) {
    /**
    Validate the field that has to contain a non-empty string.
    **/
    trimField(field);
    var valid = Boolean(field.value);
    showFieldValidation(field, valid);
    return valid;
}

function validateBook(form) {
    /**
    Validate new/edit book form. To be called from onAction.

    Actual validation happens onchange(), this function only
    looks for HTML objects with INVALID_CLASSNAME.
    **/
    if ("createEvent" in document) {
        var evnt = document.createEvent("HTMLEvents");
        evnt.initEvent("change",false,true);
        function runOnChange(field) {
            field.dispatchEvent(evnt);
        };
    } else {
        function runOnChange(field) {
            field.fireEvent("onchange");
        };
    };

    var i;
    total = form.length;
    for (i=0; i<total; i++) {
        /* trigger all onchange() */
        field = form[i];
        runOnChange(field);
    };
    var valid = !Boolean(form.querySelectorAll("."+INVALID_CLASSNAME).length);
    return valid;
};

function showFieldValidation(field, valid) {
    /**
    Add INVALID_CLASSNAME to the field.className if ISBN is not valid.
        @param {object} field - HTML object that supports "class" attribute
        @param {boolean} valid - validation status
        @returns {void}
    **/
    if (valid) {
        field.className = field.className.replace(INVALID_CLASSNAME, "");
    } else {
        if (field.className.indexOf(INVALID_CLASSNAME) === -1) {
            field.className = field.className + " " + INVALID_CLASSNAME;
        };
    };
};

function fillByISBN(xhttp) {
    /**
    Fill input form based on new ISBN entered by user.
    Callback function for AJAX request.
        @param  {object} xhttp - XMLHttpRequest object
        @returns {void}
    **/
    var reply = xhttp; //xhttp.responseText; //DEBUG //TODO:switch back to responseText
    var bookData = JSON.parse(reply);
    var form = document.forms["edit_book"];
    for (var key in bookData) {
        if (form[key]) {
            form[key].value = bookData[key];
        };
    };
    //TODO: handle base64 thumbnails
};

function newISBN(field) {
    /**
    Process new ISBN entered by user.
        @param   {object} field - the <input> field on HTML page
        @returns {void}
    **/
    trimField(field);
    validateISBN(field);
    if ((field.className.indexOf(INVALID_CLASSNAME) === -1)
    && cleanISBN(field.value).length) {
        ajaxLoad(AJAX_URL + "?isbn=" + cleanISBN(field.value), fillByISBN);
    };
};

function validateISBN(field) {
    /**
    Validate ISBN typed in by user.
        @param   {object} field - the <input> field on HTML page.
        @returns {void}
    **/
    var isbn = field.value;
    var validity = (isValidISBN(isbn) || cleanISBN(isbn).length===0);
    showFieldValidation(field,validity);
};

function isValidISBN(s) {
    /**
    Check if string represents a valid ISBN.
        @param   {string}  s
        @returns {boolean}
    **/
    var valid = false;
    var alphanum = cleanISBN(s);
    if ((alphanum.length === 10 || alphanum.length === 13)) {
        valid = true;
    };
    return valid;
};

function cleanISBN(s) {
    /** Clean up ISBN string **/
    return s.replace(/[^a-z0-9]/gi,"").toUpperCase();
};

function and() {
    /**
    Perform logical AND with all parameters.
        @returns {boolean}
    **/
    result = arguments[0]
    for (i=1; i<arguments.length; i++) {
        result = result && arguments[i];
        if (!(result)) {
            break;
        };
    };
    return Boolean(result);
};
