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
% include('pagination', **locals())
