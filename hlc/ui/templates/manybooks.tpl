% rebase("main", title="Все книги")

% for book in books:
    <p>{{book.id}}, <a href="/books/{{id.encode(book.id)}}">{{book.name}}</a></p>
% end
