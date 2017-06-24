% rebase("main")
<form class="add user_input" method="post">
    <label class="field">Создать: <input name="add" type="text"/></label>
</form>
% if get("message"):
<div class="message">{{message}}</div>
% end
<ul class="items">Существующие:
% for item in get("items", set()):
<li class="item">
% if get("link"):
<a href="{{link[0] % getattr(item, link[1])}}"><span>{{getattr(item, attr)}}</span></a>
% else:
<span>{{getattr(item, attr)}}</span>
% end
</li>
% end
</ul>
