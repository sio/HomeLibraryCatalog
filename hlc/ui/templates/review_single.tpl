<%
rebase('main')
include('book_preview', **locals())
%>
<div class="review_container">
<h2>Отзыв</h2>
% if full:
<a href="{{ info['url'].path }}/edit" class="edit">[изменить]</a>
% end
<div class="info_line">
{{ reviewer.fullname or reviewer.name }},
{{ review.date.strftime(info['date_format']) }}
</div>
<% include('stars', stars=review.rating) %>
<div class="review_text">{{ !review.html }}</div>
</div>
