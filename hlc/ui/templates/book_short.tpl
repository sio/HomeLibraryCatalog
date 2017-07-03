% from hlc.items import Series, Author, Tag
% book_url = "/books/%s" % id.book.encode(book.id)
<div class="book_short clearfix">

<a href="{{book_url}}">
<h2>{{book.name}}
% authors = book.getconnected(Author)
% if authors and not "author" in hide:
- \\
% for num, author in enumerate(authors):
{{num and ", " or ""}}{{author.name.replace(",","")}}\\
% end
% end
% if book.year:
 ({{book.year}})
% end
</h2>
</a>

% series = book.getconnected(Series, order="type")
% if series:
<div class="info">
% first = True
% for s in series:
% if not first:
, 
% end
% first = False
<span class="info_line">
% num_info = str()
% if s.type:
% num_info += s.type
% end
% position = s.position(book)
% if position:
%   if num_info: num_info += ", "
%   end
%   num_info += "книга %d" % position
%   if s.number_books:
%       num_info += " из %d" % s.number_books
%   end
% end
% if num_info:
%   num_info = num_info.join("()")
% end
<a href="/series/{{id.series.encode(s.id)}}">{{s.name}}</a> {{num_info or ""}}</span>\\
% end
</div>
% end
</div>
