let userId = null;

$(function () {
  requireLogin();

  const params = new URLSearchParams(location.search);
  const mode = params.get("mode");
  userId = params.get("id");

  if (mode === "me") {
    loadMe();
  } else if (userId) {
    loadUser(userId);
  } else {
    alert("잘못된 접근입니다.");
    location.href = "index.html";
  }

  $("#updateBtn").on("click", updateUser);
  $("#deleteBtn").on("click", deleteUser);
  $("#uploadBtn").on("click", uploadProfileImage);
});

function loadMe() {
  $.ajax({
    url: API_BASE_URL + "/me",
    type: "GET",
    headers: authHeaders(),
    success: function (user) {
      userId = user.id;
      renderUser(user);
    },
    error: function (xhr) {
      if (handleAuthError(xhr)) return;
      alert(getErrorMessage(xhr));
    }
  });
}

function loadUser(id) {
  $.ajax({
    url: API_BASE_URL + "/users/" + id,
    type: "GET",
    headers: authHeaders(),
    success: function (user) {
      renderUser(user);
    },
    error: function (xhr) {
      if (handleAuthError(xhr)) return;
      alert(getErrorMessage(xhr));
    }
  });
}

function renderUser(user) {
  $("#profilePreview").attr("src", getImageUrl(user));
  $("#profileName").text(user.username);
  $("#profileEmail").text(user.email);
  $("#profileCreatedAt").text("가입일: " + user.created_at);

  $("#editUsername").val(user.username);
  $("#editEmail").val(user.email);
}

function updateUser() {
  const username = $("#editUsername").val().trim();
  const email = $("#editEmail").val().trim();
  const password = $("#editPassword").val().trim();

  const data = {};

  if (username) data.username = username;
  if (email) data.email = email;
  if (password) data.password = password;

  $.ajax({
    url: API_BASE_URL + "/users/" + userId,
    type: "PUT",
    headers: authHeaders(),
    contentType: "application/json",
    data: JSON.stringify(data),
    success: function (user) {
      alert("수정 완료");
      $("#editPassword").val("");
      renderUser(user);
    },
    error: function (xhr) {
      if (handleAuthError(xhr)) return;
      alert(getErrorMessage(xhr));
    }
  });
}

function deleteUser() {
  if (!confirm("정말 삭제하시겠습니까?")) return;

  $.ajax({
    url: API_BASE_URL + "/users/" + userId,
    type: "DELETE",
    headers: authHeaders(),
    success: function () {
      alert("삭제 완료");
      location.href = "index.html";
    },
    error: function (xhr) {
      if (handleAuthError(xhr)) return;
      alert(getErrorMessage(xhr));
    }
  });
}

function uploadProfileImage() {
  const file = $("#profileFile")[0].files[0];

  if (!file) {
    alert("업로드할 이미지를 선택하세요.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  $.ajax({
    url: API_BASE_URL + "/users/" + userId + "/profile-image",
    type: "POST",
    headers: authHeaders(),
    data: formData,
    processData: false,
    contentType: false,
    success: function (res) {
      alert("이미지 업로드 완료");
      $("#profilePreview").attr("src", API_BASE_URL + res.profile_image.url);
    },
    error: function (xhr) {
      if (handleAuthError(xhr)) return;
      alert(getErrorMessage(xhr));
    }
  });
}