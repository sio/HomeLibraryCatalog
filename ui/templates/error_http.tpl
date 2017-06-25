% rebase("main", title="Ошибка %d" % error.status_code)
<%
notes = {
    404: "Страница не найдена",
    403: "Отказано в доступе",
}
%>


<span class="info">
<p>{{notes.get(error.status_code) or error.status}}</p>
<p>{{error.body}}</p>
</span>
