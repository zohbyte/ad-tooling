import { useEffect, useState } from "react";
import { API_BASE_PATH } from "../const";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [required, setRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState(
    () => sessionStorage.getItem("tulip_auth_pass") || ""
  );

  useEffect(() => {
    fetch(`${API_BASE_PATH}/auth/required`)
      .then((r) => {
        if (!r.ok) {
          throw new Error(`API returned ${r.status}`);
        }
        return r.json();
      })
      .then((data) => {
        setRequired(!!data.required);
        if (!data.required || sessionStorage.getItem("tulip_auth_pass")) {
          setReady(true);
        }
      })
      .catch((err) => {
        setError(
          `Cannot reach Tulip API (${err.message}). ` +
            "Run: docker compose logs api schema-init"
        );
      });
  }, []);

  const onLogin = () => {
    sessionStorage.setItem("tulip_auth_user", "tulip");
    sessionStorage.setItem("tulip_auth_pass", password);
    setError(null);
    setReady(true);
  };

  if (error) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#0f1419",
          color: "#e7ecf3",
          padding: "1rem",
        }}
      >
        <div style={{ maxWidth: 520 }}>
          <h2 style={{ marginBottom: "0.5rem" }}>Tulip unavailable</h2>
          <p style={{ color: "#f87171", marginBottom: "1rem" }}>{error}</p>
          {required && (
            <>
              <p style={{ color: "#8fa3bf", marginBottom: "0.5rem" }}>
                If the API is up, enter your Tulip password:
              </p>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onLogin()}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  marginBottom: "0.75rem",
                  borderRadius: 6,
                  border: "1px solid #2d3a4f",
                  background: "#1a2332",
                  color: "#e7ecf3",
                }}
                placeholder="Password"
              />
              <button
                onClick={onLogin}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  borderRadius: 6,
                  border: "none",
                  background: "#3b82f6",
                  color: "white",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Continue
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  if (ready) return <>{children}</>;

  if (!required) return <>{children}</>;

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0f1419",
        color: "#e7ecf3",
      }}
    >
      <div style={{ width: 320 }}>
        <h2 style={{ marginBottom: "0.5rem" }}>Tulip</h2>
        <p style={{ color: "#8fa3bf", marginBottom: "1rem" }}>
          Enter the Tulip password to continue.
        </p>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onLogin()}
          style={{
            width: "100%",
            padding: "0.5rem",
            marginBottom: "0.75rem",
            borderRadius: 6,
            border: "1px solid #2d3a4f",
            background: "#1a2332",
            color: "#e7ecf3",
          }}
          placeholder="Password"
        />
        <button
          onClick={onLogin}
          style={{
            width: "100%",
            padding: "0.5rem",
            borderRadius: 6,
            border: "none",
            background: "#3b82f6",
            color: "white",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Unlock
        </button>
      </div>
    </div>
  );
}
