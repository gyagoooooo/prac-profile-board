$(function () {
  requireLogin();
  loadUsers();
});

function loadUsers() {
  $.ajax({
    url: API_BASE_URL + "/users",
    type: "GET",
    headers: authHeaders(),
    success: function (users) {
      renderUsers(users);
    },
    error: function (xhr) {
      if (handleAuthError(xhr)) return;
      alert(getErrorMessage(xhr));
    }
  });
}

function renderUsers(users) {
  const $userList = $("#userList");
  $userList.empty();

  if (users.length === 0) {
    $userList.html("<p>등록된 사용자가 없습니다.</p>");
    return;
  }

  users.forEach(function (user) {
    const imageUrl = getImageUrl(user);

    const card = `
      <div class="user-card" onclick="location.href='detail.html?id=${user.id}'">
        <img src="${imageUrl}" alt="프로필 이미지">
        <h3>${user.username}</h3>
        <p>${user.email}</p>
      </div>
    `;

    $userList.append(card);
  });
}