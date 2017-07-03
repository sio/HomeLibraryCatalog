% single_tpl = get("single_tpl") or "book_preview"

% from bottle import template
% count = 0
% for book in books:
{{!template(single_tpl, book=book, id=id, DATE_FORMAT=info["date_format"], hide=get("hide", set()))}}
% count += 1
% end

% if not count:
<div class="empty">Книг, соответствующих запросу, не найдено</div>
% end

<div class="page_nav">
% if pg_info[0] and pg_info[1]:
<a class="prev" href="{{'?p=%s&ps=%s' % (pg_info[0]-1,pg_info[1])}}">&lt; назад </a>
% end
% if count == pg_info[1] and pg_info[1]:
<a class="next" href="{{'?p=%s&ps=%s' % (pg_info[0]+1,pg_info[1])}}"> далее &gt;</a>
% end
</div>