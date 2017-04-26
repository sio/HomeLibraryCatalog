<%
rebase("main")
simple_fields = (
    ("Название книги", "title", book.name or "", "checkRequiredField(this)",
        "ajaxGetSuggestions(this)"),
    ("Издательство", "publisher", book.publisher or "", "trimField(this)", ""),
    ("Год выпуска", "year", book.year or "", "checkYearField(this)", ""),
    ("Цена", "price", book.price or "", "checkPriceField(this)", ""),
    )
%>

<form name="edit_book" class="user_input" method="post"
onsubmit="return validateBook(this)" enctype="multipart/form-data">
    <label class="field">ISBN:
        <input type="text" name="isbn" value="{{book.isbn or ""}}"
        onchange="checkISBN(this)"/>
    </label>
    <label for="author" class="field">Автор:
    % for a in authors:
        <span class="field"><input id="author" type="text"
        name="author" value="{{a.name or ""}}" onchange="trimField(this)"/>
        <a class="plus" onclick="return cloneInputContainer(this);"
        href="/nojs">[+]</a></span>
    % end
    </label>
    % for label, name, value, validate, keyup in simple_fields:
    <label class="field">{{label}}:
        <input type="text" name="{{name}}" value="{{value}}"
        onchange="{{validate}}" onkeyup="{{keyup}}"/>
    </label>
    % end
    <label class="field">Поступление:
    <div class="field center clearfix">
        <input class="first_of_3" type="text" name="in_date"
        value="{{info['date']}}" onchange="checkDateField(this)"/>
        <input class="second_of_3" type="text" name="in_type"
        placeholder="тип поступления" onchange="trimField(this)"/>
        <input class="third_of_3" type="text" name="in_comment"
        placeholder="комментарий" onchange="trimField(this)"/>
    </div>
    </label>
    <label class="field">Выбытие:
    <div class="field center clearfix">
        <input class="first_of_3" type="text" name="out_date"
        onchange="checkDateField(this)"/>
        <input class="second_of_3" type="text" name="out_type"
        placeholder="тип выбытия" onchange="trimField(this)"/>
        <input class="third_of_3" type="text" name="out_comment"
        placeholder="комментарий" onchange="trimField(this)"/>
    </div>
    </label>
    <label class="field">Серия/цикл:<span class="field clearfix">
        <input class="series_type" type="text" name="series_type" placeholder="тип цикла"/>
        <input class="series_name" type="text" name="series_name" placeholder="цикл"/>
        <input class="number" type="text" name="book_no" placeholder="#"/>
        <input class="number" type="text" name="total" placeholder="##"/>
        <a class="plus" onclick="return cloneInputContainer(this);"
        href="/nojs">[+]</a>
    </span></label>
    <label class="field">Картинка:
    <span>
        <a href="/nojs" onclick="return switchChildren(this);"
        data-switch-to="file">из файла</a>,
        <a href="/nojs" onclick="return switchChildren(this);"
        data-switch-to="url">по ссылке</a>,
        <a href="/nojs" onclick="return switchChildren(this);"
        data-switch-to="auto">автоматический поиск</a>
        <input type="text" name="thumb_url" placeholder="Адрес в интернет (URL)"
        data-switch="url" hidden="true"/>
        <input type="text" name="thumb_filename" placeholder="Выберите файл"
        onfocus="getFileInput(this); this.onfocus()"
        data-file-input="thumbnail" data-switch="file"/>
        <input type="text" data-switch="auto" value="ПОКА НЕ РАБОТАЕТ"
        hidden="true"/>
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
    <input class="field" type="submit" value="OK"/>
</form>
