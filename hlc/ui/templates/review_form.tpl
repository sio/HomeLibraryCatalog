<%
rebase('main')
onload = 'updateStarStatus();'
include('book_preview', **locals())
%>
<h2>Отзыв</h2>
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
    <span class="field">
    {{ !form.rating.label }}
    {{ !form.rating(class_="stars", onchange="updateStarStatus();") }}
    </span>

    <span class="field">
    {{ !form.review.label }}
    {{ !form.review }}
    </span>

    <span class="field">
    {{ !form.submit }}
    </span>
</form>
