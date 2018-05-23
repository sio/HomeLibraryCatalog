<%
rebase('main')

for review in reviews:
%>
<div><a href="/reviews/{{ id.review.encode(review.id) }}">{{ review.rating }}</a></div>
<div>{{ review.html }}</div>
<%
end
%>

