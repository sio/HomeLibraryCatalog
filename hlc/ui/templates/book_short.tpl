% import itertools
% from hlc.items import Series, Author, Tag
% book_url = "/books/%s" % id.book.encode(book.id)
<div class="book_short clearfix">

<a href="{{book_url}}">
<h2>{{book.name}}
% authors = book.getconnected(Author)
% if authors and not "author" in hide:
- \\
%   max_authors = 3
%   names = [ author.name.replace(",","") for author in itertools.islice(authors,max_authors+1) ]
%   if len(names) > max_authors:
%       names.pop()
%       names_suffix = " и др."
%   else:
%       names_suffix = ""
%   end
{{  ', '.join(names) + names_suffix }}
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
