% from hlc.items import Series, Author, Tag
% book_url = "/book/%s" % id.book.encode(book.id)
<div class="book_preview clearfix">

<a href="{{book_url}}">
<h2>{{book.name}}
% authors = book.getconnected(Author)
% if authors:
(\\
% for num, author in enumerate(authors):
{{num and ", " or ""}}{{author.name.replace(",","")}}\\
% end
)\\
% end
</h2>
</a>

% if book.thumbnail_id:
<div class="thumb">
    <a href="{{book_url}}">
        <img src="/thumbs/{{id.thumb.encode(book.thumbnail_id)}}"/>
    </a>
</div>
% end

<div class="description">

% if book.annotation:
<div class="annotation">
% TRUNCATE_CHARS = 300
{{book.annotation[:TRUNCATE_CHARS]}}{{book.annotation[TRUNCATE_CHARS:] and "..." or ""}}
</div>
% end

% series = book.getconnected(Series)
% if series:
<div class="info_line">
% for s in series:
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
<a href="/series/{{id.series.encode(s.id)}}">{{s.name}}</a> {{num_info or ""}}<br/>
% end
</div>
% end

% info_line2 = list()
% if book.year:
%   info_line2.append(str(book.year))
% end
% if book.publisher:
%   info_line2.append(str(book.publisher))
% end
% if book.isbn:
%   info_line2.append("ISBN:" + str(book.isbn))
% end
% if info_line2:
<div class="info_line">{{" – ".join(info_line2)}}</div>
% end

% tags = book.getconnected(Tag)
% if tags:
<div class="info_line">
% first_tag = True
% for t in tags:
%   if not first_tag:
,
%   end
%   first_tag = False
<a href="/tag/{{t.name}}" class="tag">{{t.name}}</a>\\
% end
</div>
% end
</div>
</div>
