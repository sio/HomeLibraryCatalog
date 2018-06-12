<%
from hlc.items import Book, User, Author
hide = get('hide', set())
one_book = bool(get('book', False))
if one_book:
    hide.add('header')
    if 'book' not in hide:
        include('book_preview', **locals())
    end
end
count = 0
for review in reviews:
    count += 1
    if count == page.size:
        break
    end
    book = next(review.getconnected(Book))
    review_author = next(review.getconnected(User))
%>
<div class="review_short">
<% if 'header' not in hide: %>
    <h2>
    <a href="/books/{{ id.book.encode(book.id) }}">{{ book.name }}</a>
    <span class="authors">
        <%
        empty = True
        for author in book.getconnected(Author):
            if empty:
        %>
        (\\
        <%
            empty = False
            end
        %>
<a class="author" href="/authors/{{ id.author.encode(author.id) }}">{{ author.name.replace(',','') }}</a>\\
        <%
        end
        if not empty:
        %>
)
        <%
        end
        %>
    </span>
    </h2>
<% end %>
    <span class="info_line">
    <a href="/reviews/{{id.review.encode(review.id) }}">
    {{ review_author.fullname or review_author.name }},
    {{ review.date.strftime(info['date_format']) }}
    </a>
    </span>
    <% include('stars', stars=review.rating) %>
    <div class="review_text">{{! review.html }}</div>
</div>
<%
end
%>

