import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { clearToken, getToken, setToken } from "../lib/auth";
import "./PrivateGate.css";

interface Props {
  children: React.ReactNode;
}

export default function PrivateGate({ children }: Props) {
  const [token, setTokenState] = useState(getToken());
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(!!token);

  useEffect(() => {
    if (!token) {
      setChecking(false);
      return;
    }
    api.adminGetArticles(token).catch(() => {
      clearToken();
      setTokenState("");
      setChecking(false);
    }).finally(() => setChecking(false));
  }, [token]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const { access_token } = await api.login(password);
      setToken(access_token);
      setTokenState(access_token);
      setPassword("");
    } catch {
      setError("Invalid password");
    }
  };

  if (checking) {
    return <p className="private-loading mono">Verifying…</p>;
  }

  if (!token) {
    return (
      <div className="private-login">
        <div className="private-login-card card">
          <h1 className="serif">Private</h1>
          <p className="private-login-desc">Sign in to access your personal pages.</p>
          <form onSubmit={handleLogin}>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
            />
            {error && <p className="private-error">{error}</p>}
            <button type="submit" className="btn btn-primary">Sign in</button>
          </form>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
