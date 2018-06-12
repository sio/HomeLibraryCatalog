<%
rebase('main')
count = include('review_list', **locals())['count']
include('pagination', **locals())
%>

