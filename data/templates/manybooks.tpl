% rebase("main", title="Все книги")

% for book in books:
    {{book.id}}, {{book.name}}
% end
