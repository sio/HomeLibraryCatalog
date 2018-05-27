<%
# TODO: add pagination!
rebase('main')

from hlc.items import Book, User, Author

for review in reviews:
    book = next(review.getconnected(Book))
    review_author = next(review.getconnected(User))
%>
<div class="review_short">
    <a href="/books/{{ id.book.encode(book.id) }}"><h2>{{ book.name }}</h2></a>
    <div class="authors info_line">
<% for author in book.getconnected(Author): %>
<a class="author" href="/authors/{{ id.author.encode(author.id) }}">{{ author.name.replace(',','') }}</a>\\
<% end %>
    </div>
    <% include('stars', stars=review.rating) %>
    <a href="/reviews/{{id.review.encode(review.id) }}">
    <span class="info_line">
    {{ review.date.strftime(info['date_format']) }}, {{ review_author.fullname or review_author.name }}
    </span>
    </a>
    <div class="review_text">{{! review.html }}</div>
</div>
<%
end
%>

