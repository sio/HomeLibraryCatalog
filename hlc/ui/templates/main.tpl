<%
app_name = info.get("title") or "Библиотека"
user = get("user", None)
url = info["url"]
if url[2] == "/search":
    from urllib.parse import parse_qs
    search_query = parse_qs(url[3]).get("q", [""])[0]
else:
    search_query = ""
end
%>
<!DOCTYPE html>
<html>
<head>
    <title>{{"%s [%s]" % (title, app_name)}}</title>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <link rel="stylesheet" type="text/css" href="/static/theme.css?v20180911"/>
    <script src="/static/theme.js?v20180910"></script>
</head>
<body onload="{{get('onload') or ''}}">
<div id="header" class="widewrapper no_print">
    <a href="/"><h1>{{app_name}}</h1></a>
    <form id="quick_search" name="search" action="/search">
        <input name="q" type="text" placeholder="поиск" value="{{search_query}}"/>
    </form>
</div>
<div id="middle">
    <div id="menu" class="no_print">
        <ul>
        <li><a href="/books">Книги</a></li>
        <li><a href="/books/add">Добавить книгу</a></li>
        <li><a href="/queue">Очередь штрих-кодов</a></li>
        <li class="with_separator"><a href="/reviews">Отзывы</a></li>
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
