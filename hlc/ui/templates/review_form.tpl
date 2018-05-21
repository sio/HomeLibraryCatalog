<%
rebase('main')
%>
<form
    name="review"
    class="user_input"
    method="post"
>
    {{ !form.rating.label }}
    {{ !form.rating }}

    {{ !form.review.label }}
    {{ !form.review }}

    {{ !form.submit }}
</form>
