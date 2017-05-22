% rebase("main", title="Ошибка %d" % error.status_code)
<%
notes = {
    404: "Страница не найдена",
}
%>


<span class="info">
<p>{{notes.get(error.status_code) or error.status}}</p>
<p>{{error.body}}</p>
</span>
