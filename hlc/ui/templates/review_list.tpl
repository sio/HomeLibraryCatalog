<%
# TODO: add pagination!
rebase('main')

from hlc.items import Book, User, Author

for review in reviews:
    book = next(review.getconnected(Book))
    review_author = next(review.getconnected(User))
%>
<div class="review_short">
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

