% rebase("main", title="Список штрих-кодов")
<form class="scan_barcode user_input" name="new_barcode">
    <label class="field">Добавить:
        <input name="isbn" type="text" placeholder="штрих-код / ISBN"/>
    </label>
</form>
% if get("message"):
<div class="message">{{message}}</div>
% end
<ul class="items">Ранее добавлены:
% for barcode in get("barcodes", set()):
<li class="barcode">
    <a class="add" href="/books/add?isbn={{barcode.isbn}}">{{barcode.isbn}}</a>
    <a class="del" href="/queue?isbn={{barcode.isbn}}&delete=yes">[x]</a>
</li>
% end
</ul>
