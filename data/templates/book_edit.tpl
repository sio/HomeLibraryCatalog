<%
rebase("main")
simple_fields = (
    ("Название книги", "title", book.name or "", "checkRequiredField(this)",
        "ajaxSuggestions(event)"),
    ("Издательство", "publisher", book.publisher or "", "trimField(this)", 
        "ajaxSuggestions(event)"),
    ("Год выпуска", "year", book.year or "", "checkYearField(this)", ""),
    ("Цена", "price", book.price or "", "checkPriceField(this)", ""),
    )
%>

<form name="edit_book" class="user_input" method="post"
onsubmit="return validateBook(this)" enctype="multipart/form-data">
    <label class="field">ISBN:
        <input type="text" name="isbn" value="{{book.isbn or ""}}"
        onchange="checkISBN(this); ajaxISBN(this)"/>
    </label>
    <label for="author" class="field">Автор:
    % for a in authors:
        <span class="field"><input id="author" type="text"
        name="author" value="{{a.name or ""}}" onchange="trimField(this)"
        onkeypress="ajaxSuggestions(event)"/>
        <a class="plus" onclick="return cloneInputContainer(this);"
        href="/nojs">[+]</a></span>
    % end
    </label>
    % for label, name, value, validate, keyup in simple_fields:
    <label class="field">{{label}}:
        <input type="text" name="{{name}}" value="{{value}}"
        onchange="{{validate}}" onkeypress="{{keyup}}"/>
    </label>
    % end
    <label class="field">Поступление:
    <div class="field center clearfix">
        <input class="first_of_3" type="text" name="in_date"
        placeholder="дд.мм.гггг" value="{{info['date']}}"
        onchange="checkDateField(this)"/>
        <input class="second_of_3" type="text" name="in_type"
        placeholder="тип поступления" onchange="trimField(this)"
        onkeypress="ajaxSuggestions(event)"/>
        <input class="third_of_3" type="text" name="in_comment"
        placeholder="комментарий" onchange="trimField(this)"
        onkeypress="ajaxSuggestions(event)"/>
    </div>
    </label>
    <label class="field">Выбытие:
    <div class="field center clearfix">
        <input class="first_of_3" type="text" name="out_date"
        placeholder="дд.мм.гггг" onchange="checkDateField(this)"/>
        <input class="second_of_3" type="text" name="out_type"
        placeholder="тип выбытия" onchange="trimField(this)"
        onkeypress="ajaxSuggestions(event)"/>
        <input class="third_of_3" type="text" name="out_comment"
        placeholder="комментарий" onchange="trimField(this)"
        onkeypress="ajaxSuggestions(event)"/>
    </div>
    </label>
    <label class="field">Аннотация:
    <textarea class="field" name="annotation"
    onchange="trimField(this)"></textarea>
    </label>
    <label class="field">Серия/цикл:<span class="field one_line clearfix">
        <input class="series_type" type="text" name="series_type"
        placeholder="тип" onchange="trimField(this)" onkeypress="ajaxSuggestions(event)"/>
        <input class="series_name" type="text" name="series_name"
        placeholder="наименование"
        onkeypress="ajaxSuggestions(event)"
        onkeyup="showSeriesNumbers(this)"
        onchange="trimField(this)"/>
        <span class="numbers field">
        <input class="number" type="text" name="book_no" placeholder="#"
        onchange="checkPositiveInt(this)"/>  из
        <input class="number" type="text" name="total" placeholder="##"
        onchange="checkPositiveInt(this)"/>
        </span class="field">
        <a class="plus" onclick="return cloneInputContainer(this);"
        href="/nojs">[+]</a>
    </span></label>
    <label class="field">Картинка:
    <span>
        <a href="/nojs" onclick="return switchChildren(this, true);"
        data-switch-to="file">из файла</a>,
        <a href="/nojs" onclick="return switchChildren(this, true);"
        data-switch-to="url">по ссылке</a>,
        <a href="/nojs" onclick="return switchChildren(this, true);"
        data-switch-to="auto">автоматический поиск</a>
        <input type="text" name="thumb_url" placeholder="Адрес в интернет (URL)"
        data-switch="url" hidden="true" onchange="trimField(this)"/>
        <input type="text" name="thumb_filename" placeholder="Выберите файл"
        onfocus="getFileInput(this); this.onfocus()"
        data-file-input="thumbnail" data-switch="file"/>
        <input type="text" data-switch="auto" placeholder="ПОКА НЕ РАБОТАЕТ"
        hidden="true" disabled="true"/>
    </span>
    </label>
    <label class="field">Другие файлы:
    <span class="field">
    <input type="text" data-file-input="upload" placeholder="Выберите файл"
    onfocus="getFileInput(this); this.onfocus()"/>
    <a class="plus" onclick="return cloneInputContainer(this);"
    href="/nojs">[+]</a>
    </span>
    </label>
    <label class="field">Теги:
    <input type="text" name="tags" placeholder="список категорий через запятую"
    onkeypress="ajaxCSV(event)" onchange="trimField(this)"/>
    </label>
    <input class="field" type="submit" value="OK"/>
</form>
