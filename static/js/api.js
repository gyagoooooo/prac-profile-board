const API_BASE_URL = "";

function getToken() {
  return localStorage.getItem("access_token");
}

function authHeaders() {
  return {
    Authorization: "Bearer " + getToken()
  };
}

function getErrorMessage(xhr) {
  const d = xhr.responseJSON && xhr.responseJSON.detail;

  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map(e => e.msg).join(", ");

  return "알 수 없는 오류가 발생했습니다.";
}

function requireLogin() {
  if (!getToken()) {
    alert("로그인이 필요합니다.");
    location.href = "login.html";
  }
}

function handleAuthError(xhr) {
  if (xhr.status === 401) {
    alert("로그인이 만료되었습니다. 다시 로그인해주세요.");
    localStorage.removeItem("access_token");
    location.href = "login.html";
    return true;
  }
  return false;
}

function logout() {
  localStorage.removeItem("access_token");
  location.href = "login.html";
}

function getImageUrl(user) {
  if (!user.profile_image || !user.profile_image.url) {
    return "https://via.placeholder.com/160?text=No+Image";
  }

  return API_BASE_URL + user.profile_image.url;
}