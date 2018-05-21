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
    BookReview
)
from hlc.util import (
    timestamp,
)


class ReviewForm(Form):
    rating = RadioField(
        'Рейтинг',
        [validators.Optional()],
        choices = [(n, str(n)) for n in range(1, 6)],
        coerce = int
    )
    review = TextAreaField('Отзыв', [validators.Optional()])
    submit = SubmitField('Сохранить')


def controller(webui, user, book_hexid=None, review_hexid=None):
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
            review.date = datetime.now()
            review.markup = 'plain text'
            review.review = form.review.data
            review.rating = form.rating.data
            review.save()
            redirect('/reviews/' + webui.id.review.encode(review.id))
        else:
            raise ValueError('Invalid form data: {}'.format(form.errors))

    if request.method == 'GET':  # show form
        form = ReviewForm(obj=review)
        return template(
            'review_form',
            title='Изменить отзыв' if review.saved else 'Новый отзыв',
            id=webui.id,
            info=webui.info,
            user=user,
            form=form
        )


def view_single(webui, user, hexid):
    pass
