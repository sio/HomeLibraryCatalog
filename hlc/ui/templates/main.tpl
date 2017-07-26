<%
app_name = info.get("title") or "Библиотека"
user = get("user", None)
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
    <form id="quick_search" name="search" action="/search">
        <input name="q" type="text" placeholder="поиск"/>
    </form>
</div>
<div id="middle">
    <div id="menu" class="no_print">
        <ul>
        <li><a href="/books">Каталог</a></li>
        <li><a href="/books/add">Добавить книгу</a></li>
        <li><a href="/queue">Очередь штрих-кодов</a></li>
        % if user:
        <li class="with_separator"><a href="/users/{{user.name}}">Аккаунт</a></li>
        <li><a href="/logout">Выйти</a></li>
        % else:
        <li class="with_separator"><a href="/login">Войти</a></li>
        % end
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