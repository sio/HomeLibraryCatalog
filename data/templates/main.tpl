<%
app_name = "Библиотека"
%>
<!DOCTYPE html>
<html>
<head>
    <title>{{"%s [%s]" % (title, app_name)}}</title>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" type="text/css" href="/static/theme.css"/>
    <script src="/static/theme.js"></script>
</head>
<body onload="{{get('onload') or ''}}">
<div id="header" class="widewrapper no_print">
    <a href="/"><h1>{{app_name}}</h1></a>
</div>
<div id="middle">
    <div id="menu" class="no_print">
        <ul>
        <li><a href="/table/books">Каталог</a></li>
        <li><a href="/books/add">Добавить книгу</a></li>
        <li><a href="#">Выбытие книг</a></li>
        <li><a href="/books">База данных</a></li>
        <li><a href="#">MENU5</a></li>
        <li><a href="/login">Войти</a></li>
        </ul>
    </div>
    <div id="page">
    <h1>{{title}}</h1>
    {{!base}}
    </div>
</div>
<div id="footer" class="widewrapper no_print">
    <p>Книг в каталоге: {{info.get("books_count", 0)}}</p>
    <p>Copyright Vitaly Potyarkin, {{info.get("copyright")}}</p>
</div>
</body>
</html>