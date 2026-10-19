# Authentication API handoff

This document describes the Django session-authentication endpoints intended for the React frontend.

## Local backend

Start Django from the repository root:

```bash
source venv/Scripts/activate
python manage.py runserver
```

The backend runs at `http://127.0.0.1:8000/`.

For React development, proxy requests beginning with `/api` to the Django server. This lets the browser treat the requests as same-origin and avoids unnecessary CORS and cookie problems.

Every frontend request should include:

```javascript
credentials: "include"
```

## CSRF setup

Before registration, login, or logout, request a CSRF cookie:

```http
GET /api/auth/csrf/
```

Successful response:

```json
{
  "detail": "CSRF cookie set."
}
```

Helper for reading the cookie:

```javascript
function getCookie(name) {
  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : null;
}
```

Call the CSRF endpoint before the first authentication request:

```javascript
await fetch("/api/auth/csrf/", {
  credentials: "include",
});

const csrfToken = getCookie("csrftoken");
```

Send that token in the `X-CSRFToken` header for POST requests.

## Register a driver

```http
POST /api/auth/register/
Content-Type: application/json
X-CSRFToken: <token>
```

Request:

```json
{
  "username": "newdriver",
  "password": "StrongPassword4910!",
  "email": "driver@example.com"
}
```

The email field is optional. Public registration currently creates driver accounts only.

React example:

```javascript
const response = await fetch("/api/auth/register/", {
  method: "POST",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken"),
  },
  body: JSON.stringify({ username, password, email }),
});

const data = await response.json();
```

Success: `201 Created`

```json
{
  "user": {
    "id": 3,
    "username": "newdriver",
    "email": "driver@example.com",
    "user_type": "driver"
  }
}
```

Possible errors:

- `400`: missing fields, invalid JSON, or password-validation failure
- `409`: username already exists

## Log in

```http
POST /api/auth/login/
Content-Type: application/json
X-CSRFToken: <token>
```

Request:

```json
{
  "username": "newdriver",
  "password": "StrongPassword4910!"
}
```

React example:

```javascript
const response = await fetch("/api/auth/login/", {
  method: "POST",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken"),
  },
  body: JSON.stringify({ username, password }),
});

const data = await response.json();
```

Success: `200 OK`

Possible errors:

- `400`: username or password missing
- `401`: invalid username or password
- `403`: inactive account

## Get the current user

```http
GET /api/auth/me/
```

React example:

```javascript
const response = await fetch("/api/auth/me/", {
  credentials: "include",
});

const data = await response.json();
```

Authenticated response:

```json
{
  "authenticated": true,
  "user": {
    "id": 3,
    "username": "newdriver",
    "email": "driver@example.com",
    "user_type": "driver"
  }
}
```

Unauthenticated response: `401 Unauthorized`

```json
{
  "authenticated": false
}
```

## Log out

```http
POST /api/auth/logout/
X-CSRFToken: <token>
```

React example:

```javascript
const response = await fetch("/api/auth/logout/", {
  method: "POST",
  credentials: "include",
  headers: {
    "X-CSRFToken": getCookie("csrftoken"),
  },
});

const data = await response.json();
```

Success:

```json
{
  "detail": "Logged out successfully."
}
```

## Important integration notes

- Django stores the login state in a session cookie; React should not store the user's password.
- Passwords are processed by Django's built-in password hashing system and are never returned by the API.
- Use `credentials: "include"` on every request that depends on the session.
- Obtain a fresh CSRF cookie if a POST request fails because its CSRF token is missing or stale.
- Sponsor and administrator accounts should not be created through the public driver-registration endpoint.
