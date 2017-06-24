<%
rebase("main")
from hlc.items import Group

title = "Пользователь " + subject.name
formatted_date = dict()
for prop in ("created_on", "expires_on"):
    value = getattr(subject, prop, None)
    if value:
        formatted_date[prop] = value.strftime(info["date_format"])
    else:
        formatted_date[prop] = value
    end
end

def disabled(name):
    if name in access:
        return ""
    else:
        return 'disabled="disabled"'
    end
end
%>
% if edit_link and not access:
<a href="/users/{{subject.name}}/edit" class="edit">[изменить]</a>
% end

<form name="edit_book"
      class="user_input ro_inputs"
      method="post"
      onsubmit="return validateBook(this)">
    <label class="field">Логин:
        <input type="text"
               name="name"
               value="{{subject.name}}"
               onchange="checkRequiredField(this)"
               {{!disabled('name')}}/>
    </label>
    <label class="field">Полное имя:
        <input type="text"
               name="fullname"
               value="{{subject.fullname or str()}}"
               onchange="trimField(this)"
               {{!disabled('fullname')}}/>
    </label>
    <label class="field">Дата регистрации:
        <input type="text"
               name="created_on"
               value="{{formatted_date.get('created_on') or 'очень давно'}}"
               disabled="disabled"/>
    </label>
    <label class="field">Состоит в группах:
        <input type="text"
               name="groups"
               value="{{', '.join([g.name for g in subject.getconnected(Group)])}}"
               placeholder="список групп через запятую"
               onkeypress="ajaxCSV(event)"
               onchange="trimField(this)"
               {{!disabled('groups')}}/>
    </label>
    % if "password" in access:
    <label class="field">Изменить пароль:
        <input type="password"
               name="password"
               placeholder="{{subject.expires_on and formatted_date['expires_on'] + ' закончится срок дейстия пароля' or (subject.hash and 'сохраненный пароль действителен' or 'введите новый пароль')}}"
               onkeypress="this.nextElementSibling.hidden=false"/>
        <input type="password"
               name="password_repeat"
               placeholder="повторите новый пароль"
               hidden="true"
               onchange="checkPasswordMatch(this)"/>
    </label>
    % end
    % if access:
    <span class="field buttons">
        <input class="button"
               type="button"
               onclick="location=location.href.split('/edit')[0]"
               value="Отменить"/>
        <input class="button"
               type="submit"
               value="Сохранить"/>
    </span>
    % end
</form>
