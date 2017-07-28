/*
 *
 * CONSTANTS
 *
 */
var INVALID_CLASSNAME = "invalid";
var ajaxSuggestionHandler = new AjaxHandler(ajaxSuggestionsFill);
var ajaxCSVHandler = new AjaxHandler(ajaxCSVFill);
var ajaxISBNHandler = new AjaxHandler(ajaxISBNFill);


/*
 *
 * PRETTIER FILE INPUT
 *
 */
function getFileInput(textInput, multiple) {
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
            fileInput.multiple = Boolean(multiple);
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
    // User types two letters
    // -> AJAX gets suggestions
    // -> User types third letter
    // -> Browser shows suggestions from datalist
    if (input.value.length >= 2) {
        var url="/ajax/suggest";
        var params = {"f": input.name, "q": input.value};
        input.setAttribute("list", input.name + "_suggestions");
        ajaxSuggestionHandler.get(url + "?" + encodeQueryData(params));
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
        input.onblur = function() {ajaxCSVHandler.xhr.abort()};
    };
    ajaxCSVHandler.xhr.abort();
    var url = "/ajax/complete"
    var params = {"f": input.name, "q": parseCSV(input.value).slice(-1)}
    ajaxCSVHandler.get(url + "?" + encodeQueryData(params));
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
function ajaxISBN(input) {
    var title = document.querySelector('input[name="title"]');
    if (isValidISBN(input.value) && title.value.trim().length===0) {
        var url="/ajax/fill";
        var params = {"isbn": input.value};
        ajaxISBNHandler.get(url + "?" + encodeQueryData(params));
    };
};
function ajaxISBNFill(xhr, json, force) {
    if (json === undefined) {
        var result = JSON.parse(xhr.responseText);
    } else {
        var result = JSON.parse(json);
    };
    var isbn = document.querySelector('input[name="isbn"]');
    if (force) {
        for (var i in result) {
            isbn.value = i;
            break;
        };
    };
    var data = result[cleanISBN(isbn.value)]
    if (data) {
        var field;

        // redirect
        if (data["redirect"]) {
            window.location = data["redirect"];
            return;
        };

        // thumbnail
        if (data["thumbnail"]) {
            for (var i=0; i<data["thumbnail"].length; i++) {
                addRadioThumbnail(data["thumbnail"][i]);
            };
        };

        // authors
        if (data["authors"]) {
            var author_inputs = document.querySelectorAll('input[name="author"]');
            var author_no = 0;
            var input_no = 0;
            for (author_no = 0; author_no < data["authors"].length; author_no++) {
                if (input_no < author_inputs.length) {
                    field = author_inputs[input_no];
                    input_no++;
                } else {
                    cloneInputContainer(author_inputs[0]);
                    field = document.querySelectorAll('input[name="author"]')[1];
                };
                field.value = data["authors"][author_no] || ""
            };
            for (input_no; input_no<author_inputs.length; input_no++) {
                var container = author_inputs[input_no].parentNode;
                container.parentNode.removeChild(container);
            };
        };

        // title
        if (data["title"]) {
            field = document.querySelector('input[name="title"]');
            if (field) {field.value = data["title"]};
        };

        // publisher
        if (data["publisher"]) {
            field = document.querySelector('input[name="publisher"]');
            if (field) {field.value = data["publisher"]};
        };

        // year
        if (data["year"]) {
            field = document.querySelector('input[name="year"]');
            if (field) {field.value = data["year"]};
        };

        // annotation
        if (data["annotation"]) {
            field = document.querySelector('textarea[name="annotation"]');
            if (field) {field.value = data["annotation"]};
        };

        // series
        if (data["series"]) {
            var series_inputs = document.querySelectorAll('input[name="series_name"]');
            for (var i=0; i<series_inputs.length; i++) {
                if (i===0) {
                    cloneInputContainer(series_inputs[i]);
                };
                var container = series_inputs[i].parentNode;
                container.parentNode.removeChild(container);
            };
            for (var i=0; i<data["series"].length; i++) {
                if (i>0) {
                    series_inputs = document.querySelectorAll('input[name="series_name"]');
                    cloneInputContainer(series_inputs[series_inputs.length-1]);
                    series_inputs = document.querySelectorAll('input[name="series_name"]');
                    container = series_inputs[series_inputs.length-1].parentNode;
                } else {
                    container = document.querySelector('input[name="series_name"]').parentNode
                };
                if (container) {
                    var ordered = ["series_type", "series_name", "book_no", "total"]
                    for (var f=0; f<ordered.length; f++) {
                        field = container.querySelector('input[name="'+ordered[f]+'"');
                        if (field) {
                            field.value = data["series"][i][f] || "";
                            if (ordered[f]==="series_name") {
                                showSeriesNumbers(field)
                            };
                        };
                    };
                };
            };
        };
        if (data["title"]) {
            scrollIntoViewIfNeeded(isbn.parentNode);
        }
    }
};
function keydownISBN(event) {
    if (event.keyCode === 13) {
        event.target.onchange();
        return false;
    };
};
function addRadioThumbnail(url) {
    /** Add new radio button for selecting from auto-fetched thumbnails **/
    var container = document.querySelector('*[data-switch="auto"]');

    var repeatSelector = '*[style^="background-image:"][style*="'+url+'"]'
    var repeat = container.querySelector(repeatSelector)

    if (!repeat) {
        do {
            var id = "thumbnail-" + Math.floor(Math.random()*1000);
        } while (document.getElementById(id));

        var label = document.createElement("label");
        label.style.backgroundImage = "url("+url+")";
        label.className = "thumbnail-radio";
        label.htmlFor = id;

        var dimensions = document.createElement("span");
        dimensions.className = "thumbnail-size";

        var img = new Image();
        img.src = url;
        img.onload = function() {
            dimensions.innerHTML = img.width + "x" + img.height;
        };

        var radiobutton = document.createElement("input");
        radiobutton.type = "radio";
        radiobutton.name = "thumb_radio";
        radiobutton.value = url;
        radiobutton.id = id;

        label.appendChild(dimensions);

        container.insertBefore(label, container.firstChild);
        container.insertBefore(radiobutton, container.firstChild);

        showMoreThumbsLink(container);
    }
    return container;
};
function showMoreThumbsLink(container) {
    var linkClassname = "more-thumbs"
    if (container.childElementCount < 4
    && !container.querySelector("."+linkClassname)) {
        var linkNode = document.createElement("a");
        linkNode.className = linkClassname;
        linkNode.href = "/nojs";
        linkNode.innerHTML = "[+]";
        linkNode.onclick = function() {
            var url = "/ajax/fill";
            var params = {"isbn":document.querySelector('input[name="isbn"]').value,
                          "thumbs":true}
            ajaxISBNHandler.get(url + "?" + encodeQueryData(params));
            linkNode.parentNode.removeChild(linkNode);
            return false;
        };
        container.appendChild(linkNode);
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
    var inputNodes = newNode.querySelectorAll("input")
    for (i=0; i<inputNodes.length; i++) {
        var subNode = inputNodes[i];
        subNode.value = "";
        if (subNode.onchange) {subNode.onchange();};
        if (!focus) {
            subNode.focus();
            focus = true;
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

function showThumbnailInputs(anchor) {
    var container = anchor.parentNode.parentNode;
    var hide = container.querySelector(".thumbnail_previous")
    var show = container.querySelector(".thumbnail_inputs")
    hide.style.display = "none";
    show.style.display = "inline";
    return false;
};

function switchChildren(node, clearInputs) {
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

        /* Allow only one month in the future (month is 0-based) */
        valid = valid &&
            (new Date() - new Date(year, month-1, day))/(1000*60*60*24) > -31;
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

function checkPositiveInt(field) {
    /**
    Validation function

    Checks if field.value contains positive integer or is empty,
    invalidates the field otherwise
    **/
    var num;
    var valid;
    trimField(field);
    num = parseInt(field.value);
    if (isNaN(num)) {
        num = ""
    };
    field.value = num;
    valid = num > 0;

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

function checkPasswordMatch(second) {
    /** Check that two password inputs contain the same password **/
    var first = second.previousElementSibling;
    var valid = (first.value === second.value);
    showFieldValidation(second, valid);
};

/*
 *
 * FORM VALIDATION
 *
 */
function validatePage(body) {
    /**Wrapper to be called from onload**/
    for (var i=0; i<document.forms.length; i++) {
        var form = document.forms[i];
        validateBook(form);
    };
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


/*
 *
 * HIGHLIGHT TEXT
 *
 */
function highlight(node, text) {
    /** Highlight all words from `text` in `node` **/
    var WILDCARD = "*";
    var HIGHLIGHT_CLASS = "highlight";
    var WORD_CHARS = "\\wА-ЯЁа-яё";  // because \w is not Unicode-aware

    var words = text.replace(/\s+/g, " ").split(" ");
    for (var i=0; i<words.length; i++) {
        var word = words[i].trim();

        // read wildcards and throw them away
        var wildcards = [word.slice(0, 1)===WILDCARD,
                         word.slice(-1)===WILDCARD];
        if (wildcards[0]) {word = word.slice(1)};
        if (wildcards[1]) {word = word.slice(0, -1)};

        // quote special chars
        word = word.replace(
                    /([.?*+^$\]\[\(\){}|+!:\/])-/g,
                    "\\$1");
        word = word.replace("<", "&lt;");
        word = word.replace(">", "&gt;");

        // insert word boundaries (remember that \w is not Unicode-aware)
        if (wildcards[0]) {word = "[" + WORD_CHARS + "]*" + word};
        if (wildcards[1]) {word += "[" + WORD_CHARS + "]*"};

        // search and replace
        var pattern = new RegExp("(^|>)([^<>]*?)([^"
                                    + WORD_CHARS
                                    + "]*)("
                                    + word
                                    + ")([^"
                                    + WORD_CHARS
                                    +"]|$)",
                                 "ig");
        node.innerHTML = node.innerHTML.replace(
                            pattern,
                            "$1$2$3<span class=\""
                                + HIGHLIGHT_CLASS
                                + "\">$4</span>$5");
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

function scrollIntoViewIfNeeded(element) {
    /* Vertical scroll only */
    var box = element.getBoundingClientRect();
    if (box.top < 0 || box.bottom > window.innerHeight) {
        element.scrollIntoView();
    }
}