<%
    from asb.views.user import LoginForm
    login_form = LoginForm(csrf_context=request.session)
%>\
\
<!DOCTYPE html>
<html>
<head>
    <title><%block name='title'>The Cave of Dragonflies ASB</%block></title>
    <link rel="stylesheet" href="/static/asb.css">
</head>
<body>
<section id="header">
<p style="text-align: center; margin: 0; padding: 2em; color: white;">
  banner goes here once I make it
</p>

<div id="menu">
<ul id="menu-user">
% if request.user is not None:
  <li class="menu-focus-link"><a href="/trainers/${request.user.identifier}">${request.user.name}</a></li>
  <li>Account stuff</li>
  <li>Buy stuff</li>
  <li>idk</li>
  <li><a href="/logout?csrf_token=${request.session.get_csrf_token()}">Log out</a></li>
% else:
  <li class="menu-focus-link"><a href="/register">Register</a></li>
  <li>
    <form action="/login" method="POST" id="login">
      ${login_form.csrf_token(id='login-csrf') | n}
      ${login_form.username.label() | n} ${login_form.username() | n}
      ${login_form.password.label() | n} ${login_form.password() | n}
      ${login_form.log_in() | n}
    </form>
  </li>
% endif
</ul>

<ul id="menu-dex">
  <li><a href="/trainers">Trainers</a></li>
  <li><a href="/pokemon">Pokémon</a></li>
  <li><a href="/pokemon/species">Species</a></li>
  <li><a href="/items">Items</a></li>
  <li>Moves?</li>
  <li>Abilities?</li>
</ul>
</div>
</section>

<section id="body">
${next.body()}\
</section>
</body>
</html>
