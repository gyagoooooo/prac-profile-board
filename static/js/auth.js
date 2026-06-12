$(function () {
  $("#loginBtn").on("click", login);
  $("#registerBtn").on("click", register);
});

function login() {
  const email = $("#loginEmail").val().trim();
  const password = $("#loginPassword").val().trim();

  if (!email || !password) {
    alert("이메일과 비밀번호를 입력하세요.");
    return;
  }

  $.ajax({
    url: API_BASE_URL + "/login",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      email: email,
      password: password
    }),
    success: function (res) {
      localStorage.setItem("access_token", res.access_token);
      location.href = "index.html";
    },
    error: function (xhr) {
      alert(getErrorMessage(xhr));
    }
  });
}

function register() {
  const username = $("#registerUsername").val().trim();
  const email = $("#registerEmail").val().trim();
  const password = $("#registerPassword").val().trim();

  if (!username || !email || !password) {
    alert("이름, 이메일, 비밀번호를 모두 입력하세요.");
    return;
  }

  $.ajax({
    url: API_BASE_URL + "/register",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      username: username,
      email: email,
      password: password
    }),
    success: function () {
      alert("회원가입이 완료되었습니다. 로그인해주세요.");
      location.href = "login.html";
    },
    error: function (xhr) {
      alert(getErrorMessage(xhr));
    }
  });
}