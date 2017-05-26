% rebase("main", title="Авторизация")
<form class="user_input" name="auth" method="post">
    % if error:
    <div class="info error">Введен неправильный логин или пароль</div>
    % end
    <label class="field">Пользователь
    <input name="user" type="text"></input>
    </label>
    <label class="field">Пароль
    <input name="password" type="password"></input>
    </label>
    <span class="field">
    <input type="submit" value="OK"/>
    </span>
</form>