<%
if book:
    title = "Редактировать книгу"
    onload = "validatePage(this)"
else:
    title = "Добавить книгу"
end

rebase("main")

simple_fields = (
    ("Название книги", "title", book.name or "", "checkRequiredField(this)", "ajaxSuggestions(event)"),
    ("Издательство", "publisher", book.publisher or "", "trimField(this)", "ajaxSuggestions(event)"),
    ("Год выпуска", "year", book.year or "", "checkYearField(this)", ""),
    ("Цена", "price", book.price or "", "checkPriceField(this)", ""),
)

in_date = out_date = None
if book.in_date:
    in_date = book.in_date.strftime(info["date_format"])
end
if book.out_date:
    out_date = book.out_date.strftime(info["date_format"])
end
%>

<form name="edit_book"
      class="user_input"
      method="post"
      onsubmit="return validateBook(this)"
      enctype="multipart/form-data">
    <label class="field">ISBN:
        <input type="text"
               name="isbn"
               value="{{book.isbn or ""}}"
               onkeydown="return keydownISBN(event)"
               onchange="checkISBN(this); ajaxISBN(this)"/>
    </label>
    <label for="author" class="field">Автор:
    % for a in conn["authors"]:
        <span class="field">
        <input id="author"
               type="text"
               name="author"
               value="{{a.name or ""}}"
               onchange="trimField(this)"
               onkeypress="ajaxSuggestions(event)"/>
        <a class="plus"
           onclick="return cloneInputContainer(this);"
           href="/nojs">[+]</a>
        </span>
    % end
    </label>
    % for label, name, value, validate, keyup in simple_fields:
    <label class="field">{{label}}:
        <input type="text"
               name="{{name}}"
               value="{{value}}"
               onchange="{{validate}}"
               onkeypress="{{keyup}}"/>
    </label>
    % end
    <label class="field">Поступление:
    <div class="field center clearfix">
        <input class="first_of_3"
               type="text"
               name="in_date"
               placeholder="дд.мм.гггг"
               value="{{in_date or info['date']}}"
               onchange="checkDateField(this)"/>
        <input class="second_of_3"
               type="text"
               name="in_type"
               placeholder="тип поступления"
               onchange="trimField(this)"
               onkeypress="ajaxSuggestions(event)"
               value="{{book.in_type or ''}}"/>
        <input class="third_of_3"
               type="text"
               name="in_comment"
               placeholder="комментарий"
               onchange="trimField(this)"
               onkeypress="ajaxSuggestions(event)"
               value="{{book.in_comment or ''}}"/>
    </div>
    </label>
    <label class="field">Выбытие:
    <div class="field center clearfix">
        <input class="first_of_3"
               type="text"
               name="out_date"
               placeholder="дд.мм.гггг"
               onchange="checkDateField(this)"
               value="{{out_date or ''}}"/>
        <input class="second_of_3"
               type="text"
               name="out_type"
               placeholder="тип выбытия"
               onchange="trimField(this)"
               onkeypress="ajaxSuggestions(event)"
               value="{{book.out_type or ''}}"/>
        <input class="third_of_3"
               type="text"
               name="out_comment"
               placeholder="комментарий"
               onchange="trimField(this)"
               onkeypress="ajaxSuggestions(event)"
               value="{{book.out_comment or ''}}"/>
    </div>
    </label>
    <label class="field">Аннотация:
    <textarea class="field"
              name="annotation"
              onchange="trimField(this)">{{book.annotation or ''}}</textarea>
    </label>
    <label class="field">Серия/цикл:
    % for s in conn["series"]:
    <span class="field one_line clearfix">
        <input class="series_type"
               type="text"
               name="series_type"
               placeholder="тип"
               onchange="trimField(this)"
               onkeypress="ajaxSuggestions(event)"
               value="{{s.type or ''}}"/>
        <input class="series_name"
               type="text"
               name="series_name"
               placeholder="наименование"
               onkeypress="ajaxSuggestions(event)"
               onkeyup="showSeriesNumbers(this)"
               onchange="trimField(this); showSeriesNumbers(this)"
               value="{{s.name or ''}}"/>
        <span class="numbers field">
            <input class="number"
                   type="text"
                   name="book_no"
                   placeholder="#"
                   onchange="checkPositiveInt(this)"
                   value="{{s.position(book) or ''}}"/>  из
            <input class="number"
                   type="text"
                   name="total"
                   placeholder="##"
                   onchange="checkPositiveInt(this)"
                   value="{{s.number_books or ''}}"/>
        </span>
        <a class="plus"
           onclick="return cloneInputContainer(this);"
           href="/nojs">[+]</a>
    </span>
    % end
    </label>
    <label class="field">Картинка:
    % if conn["thumbnail"]:
    <span class="thumbnail_previous">
    <img src="/thumbs/{{id.thumb.encode(conn['thumbnail'][0].id)}}"></img>
    <a href="/nojs" onclick="return showThumbnailInputs(this)">[заменить]</a>
    </span>
    <span class="thumbnail_inputs" style="display:none">
    % else:
    <span class="thumbnail_inputs">
    % end
        <a href="/nojs"
           onclick="return switchChildren(this, true);"
           data-switch-to="file">из файла</a>,
        <a href="/nojs"
           onclick="return switchChildren(this, true);"
           data-switch-to="url">по ссылке</a>,
        <a href="/nojs"
           onclick="showMoreThumbsLink(document.querySelector('.thumbnail-select'));
                    return switchChildren(this, true);"
           data-switch-to="auto">автоматический поиск</a>
        <input type="text"
               name="thumb_url"
               placeholder="Адрес в интернет (URL)"
               data-switch="url"
               hidden="true"
               onchange="trimField(this)"/>
        <input type="text"
               name="thumb_filename"
               placeholder="Выберите файл"
               onfocus="getFileInput(this); this.onfocus()"
               data-file-input="thumbnail"
               data-switch="file"/>
        <div class="thumbnail-select"
             data-switch="auto"
             hidden="true"></div>
    </span>
    </label>
    <span class="field">Другие файлы:
    % for f in conn["files"]:
    <span class="field file clearfix">
        <a href="/file/{{id.file.encode(f.id)}}"
           class="file">{{f.name}}</a>
        <label>
            <input value="{{id.file.encode(f.id)}}"
                   type="checkbox"
                   name="delete_file"/>
            [удалить]
        </label>
    </span>
    % end
    <span class="field">
        <input type="text"
               data-file-input="upload"
               placeholder="Выберите файл"
               onfocus="getFileInput(this); this.onfocus()"/>
        <a class="plus"
           onclick="return cloneInputContainer(this);"
           href="/nojs">[+]</a>
    </span>
    </span>
    <label class="field">Теги:
        <input type="text"
               name="tags"
               placeholder="список категорий через запятую"
               onkeypress="ajaxCSV(event)"
               onchange="trimField(this)"
               value="{{", ".join([t.name for t in conn['tags']])}}"/>
    </label>
    <span class="field buttons">
        <input class="button"
               type="button"
               onclick="location=location.href"
               value="Отменить"/>
        <input class="button"
               type="submit"
               value="Сохранить"/>
    </span>
</form>
