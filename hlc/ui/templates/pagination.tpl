<%
from urllib.parse import urlencode, parse_qs
params = {k:v[0] for k,v in parse_qs(info["url"][3]).items()}
last = params.pop('last', False)
if (not count) and page.num and not last:
    from bottle import redirect
    params['p'] = page.num - 1
    params['last'] = 1
    redirect('?'+urlencode(params))
end
%>
<div class="page_nav">
% if page.num and page.size:
%    params["p"] = page.num-1
<a class="prev" href="{{'?'+urlencode(params)}}">&lt; назад </a>
% end
% if count == page.size and page.size and not last:
%    params["p"] = page.num+1
<a class="next" href="{{'?'+urlencode(params)}}"> далее &gt;</a>
% end
</div>
