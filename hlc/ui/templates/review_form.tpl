<%
rebase('main')
%>
<form
    name="review"
    class="user_input"
    method="post"
>
    <%
    if form.errors:
        for field, error in form.errors.items():
    %>
        {{ field }}: {{ error }}
    <%
        end
    end
    %>
    {{ !form.rating.label }}
    {{ !form.rating }}

    {{ !form.review.label }}
    {{ !form.review }}

    {{ !form.submit }}
</form>
