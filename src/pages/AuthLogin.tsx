import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { setAuth } from "../lib/api";

export default function AuthLogin() {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const trimmedEmail = email.trim();
      const trimmedName = fullName.trim();
      const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
      const body: any = { email: trimmedEmail, password };
      if (isRegister) body.name = trimmedName;

      // Use a consistent base URL or relative path handled by proxy
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      let data: any = {};
      const contentType = res.headers.get("content-type");

      if (contentType && contentType.includes("application/json")) {
        const text = await res.text();
        if (text) {
          try {
            data = JSON.parse(text);
          } catch (e) {
            console.error("JSON parse error:", e);
            throw new Error("Invalid response from server");
          }
        }
      }

      if (!res.ok) {
        setError(data.detail || data.error || `Server error (${res.status}): Please check if the backend is running.`);
        return;
      }

      setAuth(data.token, data.user);
      navigate("/dashboard");
    } catch (err: any) {
      console.error("Auth error:", err);
      setError(err.message || "Network error — is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-900 tracking-tight">
          {isRegister ? "Create your account" : "Sign in to your account"}
        </h2>
        <p className="mt-2 text-center text-sm text-slate-600">
          {isRegister ? "Already have an account? " : "Don't have an account? "}
          <button
            onClick={() => { setIsRegister(!isRegister); setError(""); }}
            className="font-medium text-blue-600 hover:text-blue-500"
          >
            {isRegister ? "Sign in" : "Register"}
          </button>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-sm sm:rounded-2xl sm:px-10 border border-slate-200">
          {error && (
            <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700">
              {error}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>
            {isRegister && (
              <div>
                <label htmlFor="fullName" className="block text-sm font-medium text-slate-700">
                  Full Name
                </label>
                <div className="mt-1">
                  <input
                    id="fullName"
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm placeholder-slate-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm placeholder-slate-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  type="password"
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={isRegister ? "Min. 8 characters" : ""}
                  className="appearance-none block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm placeholder-slate-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
              >
                {loading ? "Please wait..." : isRegister ? "Create Account" : "Sign in"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
