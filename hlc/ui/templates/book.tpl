% rebase("main", title=book.name)
% DATE_FORMAT = info["date_format"]
% from hlc.items import Series, Author, Thumbnail, Tag, BookFile


% if book.thumbnail_id:
% img_url = "/thumbs/%s" % id.thumb.encode(book.thumbnail_id)
<a href="{{img_url}}"><img class="thumbnail" src="{{img_url}}"></img></a>
% end
% if full:
<a href="/books/{{id.book.encode(book.id)}}/edit" class="edit">[изменить]</a>
% end
<div class="library_card">

% authors = book.getconnected(Author)
% if authors:
<div class="item">
    <div class="label">Автор:</div>
    <div class="value">
    % for author in authors:
        <a href="/authors/{{id.author.encode(author.id)}}">{{author.name}}</a><br/>
    % end
    </div>
</div>
% end

% if book.name:
<div class="item">
    <div class="label">Название:</div>
    <div class="value">{{book.name}}</div>
</div>
% end

% series = book.getconnected(Series, order="type")
% if series:
<div class="item">
<div class="label">Входит в:</div>
<div class="value">
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
</div>
% end

% if book.year:
<div class="item">
    <div class="label">Год:</div>
    <div class="value">{{book.year}}</div>
</div>
% end

% if book.publisher:
<div class="item">
    <div class="label">Издательство:</div>
    <div class="value">{{book.publisher}}</div>
</div>
% end

% if book.isbn:
<div class="item">
    <div class="label">ISBN:</div>
    <div class="value">{{book.isbn}}</div>
</div>
% end

% if book.price and full:
<div class="item">
    <div class="label">Цена:</div>
    <div class="value">{{book.price}}</div>
</div>
% end

% if book.in_date and full:
<div class="item">
    <div class="label">Поступление:</div>
    <div class="value">
    {{book.in_date.strftime(DATE_FORMAT)}}
% if book.in_type or book.in_comment:
% brackets = ["(", ", ", ")"]
{{brackets[0]}}\\
% if book.in_type:
{{book.in_type}}\\
% end
% if book.in_type and book.in_comment:
{{brackets[1]}}\\
% end
% if book.in_comment:
{{book.in_comment}}\\
% end
{{brackets[2]}}
% end
    </div>
</div>
% end

% if book.out_date and full:
<div class="item">
    <div class="label">Выбытие:</div>
    <div class="value">
    {{book.out_date.strftime(DATE_FORMAT)}}
% if book.out_type or book.out_comment:
% brackets = ["(", ", ", ")"]
{{brackets[0]}}\\
% if book.out_type:
{{book.out_type}}\\
% end
% if book.out_type and book.out_comment:
{{brackets[1]}}\\
% end
% if book.out_comment:
{{book.out_comment}}\\
% end
{{brackets[2]}}
% end
    </div>
</div>
% end

% if not full:
<div class="item">
    <div class="label">Статус:</div>
    % if book.in_date and not book.out_date:
    в наличии
    % else:
    отсутствует
    % end
</div>
% end

% if book.annotation:
<div class="item">
    <div class="label">Аннотация:</div>
    <div class="value">
    % for line in book.annotation.splitlines():
    %   if line:
        <p>{{line}}</p>
    %   end
    % end
    </div>
</div>
% end

% tags = book.getconnected(Tag)
% if tags:
<div class="item">
<div class="label">Категории:</div>
<div class="value">\\
% first_tag = True
% for t in tags:
%   if not first_tag:
,
%   end
%   first_tag = False
<a href="/tag/{{t.name}}">{{t.name}}</a>\\
% end
</div>
</div>
% end

% files = book.getconnected(BookFile)
% if files and user:
<div class="item">
    <div class="label">Файлы:</div>
    <div class="value">
% for f in files:
<a href="/file/{{id.file.encode(f.id)}}">{{f.name}}</a><br/>
% end
    </div>
</div>
% end

</div>
