'''
Backend logic for book reviews
'''

from datetime import datetime
from wtforms import (
    Form,
    RadioField,
    StringField,
    SubmitField,
    TextAreaField,
    validators,
)
from bottle import (
    abort,
    redirect,
    request,
    template,
)
from hlc.items import (
    Book,
    BookReview,
    User
)
from hlc.util import (
    timestamp,
)


class ReviewForm(Form):
    '''
    Web form to create/edit book reviews
    '''
    rating = RadioField(
        'Рейтинг',
        [validators.Optional()],
        choices = [(n, str(n)) for n in range(1, 6)],
        coerce = int
    )
    review = TextAreaField('Отзыв', [validators.Optional()])
    submit = SubmitField('Сохранить')

    def validate(self):
        '''Form wide validator: either rating or review has to be filled'''
        if not super().validate():
            return False
        valid = self.review.data.strip() or self.rating.data
        if not valid:
            if not self._errors: self._errors = {}
            self._errors['__form__'] = ['Пустой отзыв нельзя сохранить',]
        return valid


def controller(webui, user, book_hexid=None, review_hexid=None):
    '''
    Server side handler for create/edit form
    '''
    review = webui.item(BookReview, review_hexid)
    if review.saved:
        book = next(review.getconnected(Book))
        if review.reviewed_by != user.id:
            abort(403, 'Вы не можете редактировать отзыв другого пользователя')
    else:
        book = webui.item(Book, book_hexid)
        if not book.saved:
            abort(404, 'Invalid book id: %s' % hexid)

    if request.method == 'POST':  # create or update
        form = ReviewForm(request.forms.decode())
        if form.validate():
            review.book_id = book.id
            review.reviewed_by = user.id
            review.markup = 'plain text'
            review.review = form.review.data
            review.rating = form.rating.data
            review.save()
            redirect('/reviews/' + webui.id.review.encode(review.id))

    if request.method == 'GET':  # show form
        form = ReviewForm(obj=review)

    # We show the form either because it's been requested via GET
    # or because the POST data did not pass validation
    return template(
        'review_form',
        title='Изменить отзыв' if review.saved else 'Новый отзыв',
        id=webui.id,
        info=webui.info,
        user=user,
        book=book,
        form=form
    )


def view_single(webui, hexid, user=None):
    review = webui.item(BookReview, hexid)
    if not review.saved:
        abort(404)
    book = next(review.getconnected(Book))
    reviewer = next(review.getconnected(User))
    return template(
        'review_single',
        title='Отзыв на книгу',
        info=webui.info,
        id=webui.id,
        **locals()
    )


def view_list(webui, user=None):
    '''Show all book reviews'''
    query = 'SELECT id FROM book_reviews ORDER BY date DESC'
    return reviews_page(**locals())


def view_by_book(webui, book_hexid, user=None):
    '''Show reviews related to the specific book'''
    book = webui.item(Book, book_hexid)
    if not book.saved:
        abort(404)
    query = 'SELECT id FROM book_reviews WHERE book_id=? ORDER BY date DESC'
    params = (book.id,)
    return reviews_page(**locals())


def reviews_page(webui, query, params=None, title=None, user=None, book=None, **ka):
    '''
    Generate reviews page from SQL query that returns their ids

    Pagination is added automatically based on URL parameters of GET request
    '''
    query = query + ' LIMIT ? OFFSET ?'

    if params is None:
        params = list()
    else:
        params = list(params)
    title = title or 'Отзывы'

    page = webui.pagination_params()
    select = webui.db.sql.iterate(
        webui.db.sql.generic(
            webui.db.connection,
            query,
            params=params + [page.size, page.offset]
        )
    )
    reviews = (BookReview(webui.db, row[0]) for row in select)
    return template(
        'review_all',
        info=webui.info,
        id=webui.id,
        **locals()
    )
