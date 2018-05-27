<%
max_stars = 5

if stars is not None:
%>
<span class="stars">\\
<% for num in range(max_stars): %>
<span class="star {{ 'checked' if num < stars else '' }}"></span>\\
<% end %>
</span>
<% end %>
