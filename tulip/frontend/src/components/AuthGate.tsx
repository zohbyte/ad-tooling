import { useEffect, useState } from "react";
import { API_BASE_PATH } from "../const";

function authHeader(password: string): string {
  return "Basic " + btoa(`tulip:${password}`);
}

async function verifyPassword(password: string): Promise<boolean> {
  const response = await fetch(`${API_BASE_PATH}/services`, {
    headers: { Authorization: authHeader(password) },
  });
  return response.ok;
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [required, setRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_PATH}/auth/required`)
      .then((r) => {
        if (!r.ok) {
          throw new Error(`API returned ${r.status}`);
        }
        return r.json();
      })
      .then(async (data) => {
        setRequired(!!data.required);
        if (!data.required) {
          setReady(true);
          return;
        }

        const saved = sessionStorage.getItem("tulip_auth_pass");
        if (saved && (await verifyPassword(saved))) {
          setReady(true);
        } else if (saved) {
          sessionStorage.removeItem("tulip_auth_pass");
          sessionStorage.removeItem("tulip_auth_user");
        }
      })
      .catch((err) => {
        setError(
          `Cannot reach Tulip API (${err.message}). ` +
            "Run: docker compose logs api schema-init"
        );
      });
  }, []);

  const onLogin = async () => {
    setError(null);
    if (!password.trim()) {
      setError("Enter a password.");
      return;
    }
    if (!(await verifyPassword(password))) {
      setError("Wrong password.");
      return;
    }
    sessionStorage.setItem("tulip_auth_user", "tulip");
    sessionStorage.setItem("tulip_auth_pass", password);
    setReady(true);
  };

  if (error && !required) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <h2>Tulip unavailable</h2>
          <p className="auth-error">{error}</p>
        </div>
      </div>
    );
  }

  if (ready) return <>{children}</>;

  if (!required) return <>{children}</>;

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <h2>Tulip</h2>
        <p className="auth-hint">Enter the Tulip password to continue.</p>
        {error && <p className="auth-error">{error}</p>}
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void onLogin()}
          placeholder="Password"
          autoFocus
        />
        <button onClick={() => void onLogin()}>Unlock</button>
      </div>
    </div>
  );
}
