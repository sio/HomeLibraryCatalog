<%
rebase("main")
simple_fields = (
    ("Название книги", "title", book.name or "", "checkRequiredField(this)", "ajaxGetSuggestions(this)"),
    ("Издательство", "publisher", book.publisher or "", "trimField(this)", ""),
    ("Год выпуска", "year", book.year or "", "checkYearField(this)", ""),
    ("Цена", "price", book.price or "", "checkPriceField(this)", ""),
    )
%>
<!--    % ("", "", book., ""), -->
 
<form name="edit_book" class="user_input" method="post" onsubmit="return validateBook(this)">
    <label class="field">ISBN:
        <input type="text" name="isbn" value="{{book.isbn or ""}}" onchange="newISBN(this)"/>
    </label>
    <label for="author">Автор:</label>
        % for a in authors:
            <span class="field"><input id="author" type="text" name="author" value="{{a.name or ""}}" onchange="trimField(this)"/>
        % end
        <a class="plus" onclick="return cloneAuthor(this);" href="/nojs">[+]</a></span>
    % for label, name, value, validate, keyup in simple_fields:
    <label class="field">{{label}}:
        <input type="text" name="{{name}}" value="{{value}}" onchange="{{validate}}" onkeyup="{{keyup}}"/>
    </label>
    % end
    <label class="field">Поступление:</label>
    <div class="field center">
        <input class="first_of_3" type="text" name="in_date" value="{{info['date']}}" onchange="checkDateField(this)"/>
        <input class="second_of_3" type="text" name="in_type" placeholder="тип поступления" onchange="trimField(this)"/>
        <input class="third_of_3" type="text" name="in_comment" placeholder="комментарий" onchange="trimField(this)"/>
    </div>
    <!--
    <label class="field">Выбор (например, автора комментария):
        <select><option>one</option><option>two</option></select>
    </label>
    -->
    <input class="field" type="submit" value="OK"/>
</form>
