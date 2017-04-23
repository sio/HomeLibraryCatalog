<!DOCTYPE html>
<html>
<head>
    <title>{{title}}</title>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" type="text/css" href="/static/theme.css"/>
    <script src="/static/theme.js"></script>
</head>
<body>
<div id="header" class="widewrapper no_print">
    <h1>Домашняя библиотека</h1>
</div>
<div id="middle">
    <div id="menu" class="no_print">
        <ul>
        <li><a href="#">Каталог</a></li>
        <li><a href="#">Поступление книг</a></li>
        <li><a href="#">Выбытие книг</a></li>
        <li><a href="#">База данных</a></li>
        <li><a href="#">MENU5</a></li>
        <li><a href="#">MENU6</a></li>
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