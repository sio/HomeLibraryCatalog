% rebase("main", title="Список штрих-кодов")
<form class="scan_barcode" name="new_barcode">
    <input name="isbn" type="text" placeholder="Добавить ISBN"/>
    <input type="submit" value="OK">
</form>
% if get("message"):
<div class="message">{{message}}</div>
% end
<div class="queue">
% for barcode in get("barcodes", set()):
<div class="barcode">
    <a class="add" href="/books/add?isbn={{barcode.isbn}}">{{barcode.isbn}}</a>
    <a class="del" href="/queue?isbn={{barcode.isbn}}&delete=yes">[x]</a>
</div>
% end
</div>
