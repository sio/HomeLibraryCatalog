% rebase("main", title="Все книги")

% for book in books:
    <p>{{book.id}}, {{book.name}}</p>
% end
