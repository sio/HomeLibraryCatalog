/*
 *
 * CONSTANTS
 *
 */
var INVALID_CLASSNAME = "invalid";
var ajaxSuggest = new AjaxHandler(ajaxSuggestionsFill);
var ajaxCSVGuess = new AjaxHandler(ajaxCSVFill);


/*
 *
 * PRETTIER FILE INPUT
 *
 */
function getFileInput(textInput, multiple=false) {
    /**
    Return hidden <input type="file"> node synced with given <input type="text">
    node. If no such file input field exists it will be created

    Arguments:
        textInput
            Existing <input type="text"> node
        multiple
            Boolean. Whether to allow selecting multiple files

    textInput has to have attribute "data-file-input" with value "name" that
    will point to <input type="file" name="name">
    **/
    var name = textInput.getAttribute("data-file-input");
    if (name) {
        // Try existing
        var fileInput = textInput.parentNode.querySelector(
            'input[type="file"][name="' + name + '"]')

        // Create new node if needed
        if (!fileInput) {
            fileInput = document.createElement("input");
            fileInput.type = "file";
            fileInput.name = name;
            fileInput.multiple = multiple;
            fileInput.style["display"] = "none";
            textInput.parentNode.insertBefore(fileInput, textInput);
        };

        // Sync with textInput
        fileInput.onchange = function() {
            textInput.value = filesShow(fileInput.files);
        };
        textInput.onfocus = function() {
            fileInput.click();
            this.blur();
        };
        textInput.onkeypress = function() {
            textInput.onfocus();
            return false;
        };

        return fileInput;
    };
};
function filesShow(files) {
    /**
    Represent files collection as human-readable string
    **/
    var show;
    if (files.length === 1) {
        show = files[0].name;
    } else if (files.length === 0) {
        show = "";
    } else {
        show = files.length + " files: ";
        var names = [];
        var i;
        for (i=0; i<files.length; i++) {
            names.push(files[i].name);
        };
        show += names.join(", ");
    };
    return show;
};


/*
 *
 * AJAX REQUESTS
 *
 */
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

function ajaxSuggestions(keypress) {
    /** Get suggestions for input field via AJAX call **/
    var input = keypress.target;
    if (input.value.length > 2) {
        var url="/ajax/suggest";
        var params = {"f": input.name, "q": input.value};
        input.setAttribute("list", input.name + "_suggestions");
        ajaxSuggest.get(url + "?" + encodeQueryData(params));
    };
};
function ajaxSuggestionsFill(xhr) {
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

function ajaxCSV(keypress) {
    /**Make AJAX request for tag completion**/
    var input = keypress.target;
    if (!input.onkeydown) {
        input.onkeydown = function(onkeydown) {
            /**Override Tab key behavior if some text is selected**/
            if ((onkeydown.keyCode === 9) && (input.selectionStart !== input.selectionEnd)) {
                input.selectionStart = input.value.length;
                input.selectionEnd = input.selectionStart;
                return false;
            };
        };
    };
    if (!input.onblur) {
        input.onblur = function() {ajaxCSVGuess.xhr.abort()};
    };
    ajaxCSVGuess.xhr.abort();
    var url = "/ajax/complete"
    var params = {"f": input.name, "q": parseCSV(input.value).slice(-1)}
    ajaxCSVGuess.get(url + "?" + encodeQueryData(params));
};
function ajaxCSVFill(xhr) {
    /**Complete tag input based on AJAX response**/
    var result = JSON.parse(xhr.responseText);
    var field
    for (field in result) {
        if (result[field].length > 0) {
            // identify input by field
            var input = document.querySelector('input[name="' + field + '"]');
            
            // store input.value.length
            var tags = parseCSV(input.value);
            var start = tags.join(", ").length
            
            // append suggestion
            var last = tags.pop()
            if (last && result[field][0].startsWith(last)) {
                tags.push(result[field][0]);
                input.value = tags.join(", ")
                input.setSelectionRange(start, input.value.length)
            };
        };
    };
};


/*
 *
 * DOM MANIPULATION
 *
 */
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

function cloneInputContainer(node) {
    /**
    Clone node that has <input> fields among children,
    clear all <input> fields, focus the first of them
    **/
    var newNode = cloneParent(node);
    var focus = false;
    var i;
    for (i=0; i<newNode.childNodes.length; i++) {
        var subNode = newNode.childNodes[i];
        if (subNode.tagName && subNode.tagName.toLowerCase() === "input") {
            subNode.value = "";
            if (subNode.onchange) {subNode.onchange();};
            if (!focus) {
                subNode.focus();
                focus = true;
            };
        };
    };
    return false;
};

function cloneParent(node) {
    /**
    Insert a copy parent node after the parent node
    **/
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
    return copy;
};


/*
 *
 * DYNAMIC HIDING OF ELEMENTS
 *
 */
function showSeriesNumbers(node) {
    var numbers = node.parentNode.querySelector(".numbers")
    if (node.value) {
        numbers.style.display = "block";
    } else {
        numbers.style.display = "none";
    };
};

function switchChildren(node, clearInputs=false) {
    var container = node.parentNode;
    var link = node.getAttribute("data-switch-to");
    if (link && container) {
        var i;
        for (i=0; i<container.childNodes.length; i++) {
            var child = container.childNodes[i];
            var anchor;
            try {
                anchor = child.getAttribute("data-switch");
            } catch(err) {};
            if (anchor) {
                if (anchor === link) {
                    child.hidden = false;
                } else {
                    child.hidden = true;
                };
            };
            if (clearInputs) {
                if (child.tagName && child.tagName.toLowerCase()==="input") {
                    child.value = "";
                };
            };
        };
    };
    return false;
};


/*
 *
 * FIELD VALIDATION
 *
 */
function trimField(field) {
    field.value = field.value.replace(/^\s+|\s+$/g,""); //trim()
};

function checkDefaultValue(field) {
    /**
    Validation function

    Clears field.value if it was not modified since the page was loaded
    **/
    trimField(field);
    if (field.value === field.defaultValue) {field.value = ""};
};

function checkDateField(field) {
    /**
    Validation function

    Checks if field.value contains the date in DD.MM.YYYY format,
    invalidates the field otherwise
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

function checkYearField(field) {
    /**
    Validation function

    Checks if field.value contains the year YYYY format,
    invalidates the field otherwise
    **/

    var year;
    var valid;
    trimField(field);
    year = parseInt(field.value);
    if (isNaN(year)) {
        year = "";
    };
    field.value = year;
    valid = (year>=1900) && (year<=2100);

    if (field.value.length === 0) {
        valid = true;
    };

    showFieldValidation(field, valid);
};

function checkPriceField(field) {
    /**
    Validation function

    Checks if field.value contains valid price or is empty,
    invalidates the field otherwise
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
    Validation function

    Checks if field.value contains a non-empty string,
    invalidates the field otherwise
    **/
    trimField(field);
    var valid = Boolean(field.value);
    showFieldValidation(field, valid);
    return valid;
}

function checkISBN(field) {
    /**
    Validate ISBN typed in by user.
        @param   {object} field - the <input> field on HTML page.
        @returns {void}
    **/
    trimField(field);
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
    return s.replace(/[^x0-9]/gi,"").toUpperCase();
};


/*
 *
 * FORM VALIDATION
 *
 */
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


/*
 *
 * UTILITY FUNCTIONS
 *
 */
function parseCSV(CSV) {
    /**Turn a single line of comma-separated values into array**/
    var items = CSV.split(",");
    var values = [];
    var i;
    for (i=0; i<items.length; i++) {
        var text = items[i].trim();
        values.push(text);
    };
    return values;
};

function encodeQueryData(data) {
    /** Encode get parameters for URL http://stackoverflow.com/a/111545 **/
    var ret = [];
    for (var d in data) {
        ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]));
    }
    return ret.join('&');
}
