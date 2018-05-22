<%
rebase('main')
include('book_preview', **locals())
%>
<div>{{ reviewer.fullname or reviewer.name }}</div>
<div>{{ review.date.strftime(info['date_format']) }}</div>
<div>{{ review.rating }}</div>
<div>{{ review.review }}</div>
