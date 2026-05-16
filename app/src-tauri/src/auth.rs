// http клиент к musictech.tech через reqwest. вызывается из rust,
// а не из js, чтобы обойти cors webview2 и иметь нормальные таймауты

use serde::{Deserialize, Serialize};
use std::time::Duration;

const API_BASE: &str = "https://musictech.tech";
const REQUEST_TIMEOUT: Duration = Duration::from_secs(15);

#[derive(Serialize, Deserialize, Clone, Debug, Default)]
pub struct User {
    pub email: String,
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub plan: Option<String>,
    #[serde(default)]
    pub role: Option<String>,
    #[serde(rename = "createdAt", default)]
    pub created_at: Option<u64>,
}

#[derive(Serialize, Clone, Debug)]
pub struct LoginResult {
    pub token: String,
    pub user: User,
}

#[derive(Deserialize)]
struct RawResponse {
    #[serde(default)]
    ok: bool,
    #[serde(default)]
    token: Option<String>,
    #[serde(default)]
    user: Option<User>,
    #[serde(default)]
    error: Option<String>,
}

fn client() -> Result<reqwest::Client, String> {
    reqwest::Client::builder()
        .timeout(REQUEST_TIMEOUT)
        .user_agent(format!("MusicTechDesktop/{}", env!("CARGO_PKG_VERSION")))
        .build()
        .map_err(|e| format!("http клиент: {e}"))
}

#[tauri::command]
pub async fn auth_login(email: String, password: String) -> Result<LoginResult, String> {
    let res = client()?
        .post(format!("{API_BASE}/api/auth/login"))
        .json(&serde_json::json!({ "email": email, "password": password }))
        .send()
        .await
        .map_err(|e| format!("сеть: {e}"))?;

    let body: RawResponse = res.json().await.map_err(|e| format!("ответ: {e}"))?;
    if !body.ok {
        return Err(body.error.unwrap_or_else(|| "неизвестная ошибка".into()));
    }
    let token = body.token.ok_or("ответ без token")?;

    // если сервер вернул user в ответе - используем его, иначе делаем
    // второй запрос к /auth/me. это страховка от старых версий api
    let user = match body.user {
        Some(u) => u,
        None => auth_me(token.clone()).await?,
    };

    Ok(LoginResult { token, user })
}

#[tauri::command]
pub async fn auth_me(token: String) -> Result<User, String> {
    let res = client()?
        .get(format!("{API_BASE}/api/auth/me"))
        .header("authorization", format!("Bearer {token}"))
        .send()
        .await
        .map_err(|e| format!("сеть: {e}"))?;

    let body: RawResponse = res.json().await.map_err(|e| format!("ответ: {e}"))?;
    if !body.ok {
        return Err(body.error.unwrap_or_else(|| "сессия истекла".into()));
    }
    body.user.ok_or_else(|| "ответ без user".into())
}

#[tauri::command]
pub async fn auth_logout(token: String) -> Result<(), String> {
    // best-effort: чистим серверную сессию, но даже при ошибке
    // считаем что вышли локально - токен убирается из store на стороне js
    let _ = client()?
        .post(format!("{API_BASE}/api/auth/logout"))
        .header("authorization", format!("Bearer {token}"))
        .send()
        .await;
    Ok(())
}
