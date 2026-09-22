import { FormEvent, useState } from "react";

import { login, User } from "./api/client";
import JobsPage from "./features/jobs/JobsPage";
import "./styles.css";

const videoUrl = "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260314_131748_f2ca2a28-fed7-44c8-b9a9-bd9acdd5ec31.mp4";

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [username, setUsername] = useState(() => localStorage.getItem("jobda_remembered_username") ?? "");
  const [password, setPassword] = useState("");
  const [rememberUsername, setRememberUsername] = useState(() => Boolean(localStorage.getItem("jobda_remembered_username")));
  const [error, setError] = useState("");

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await login(username, password);
      if (rememberUsername) localStorage.setItem("jobda_remembered_username", username);
      else localStorage.removeItem("jobda_remembered_username");
      localStorage.setItem("jobda_access_token", result.access_token);
      setUser(result.user);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "로그인에 실패했습니다.");
    }
  }

  if (user) return <JobsPage user={user} onLogout={() => { localStorage.removeItem("jobda_access_token"); setUser(null); }} />;

  return <main className="hero-page">
    <video className="hero-video" autoPlay loop muted playsInline><source src={videoUrl} type="video/mp4" /></video>
    <nav className="hero-nav"><a className="hero-logo" href="/">JOBDA<sup>®</sup></a><div className="hero-links"><a className="active" href="#home">홈</a><a href="#studio">서비스</a><a href="#about">소개</a><a href="#journal">소식</a><a href="#reach">문의</a></div><button className="liquid-glass nav-cta" onClick={() => setShowLogin(true)}>시작하기</button></nav>
    <section id="home" className="hero-content"><h1 className="animate-fade-rise">고요 속에서<br /><em>꿈이 피어나는</em><br /><em>채용의 순간.</em></h1><p className="animate-fade-rise-delay">깊이 생각하는 사람, 대담하게 만드는 사람, 자신만의 리듬으로 나아가는 사람을 위한 채용공고를 모음. 복잡한 정보 속에서도 선명한 집중과 영감을 위한 공간을 만듦.</p><button className="liquid-glass hero-cta animate-fade-rise-delay-2" onClick={() => setShowLogin(true)}>채용 여정 시작하기</button>{showLogin && <form className="hero-login liquid-glass" onSubmit={handleLogin}><label>아이디<input value={username} onChange={(event) => setUsername(event.target.value)} required /></label><label>비밀번호<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label><label className="remember-username"><input type="checkbox" checked={rememberUsername} onChange={(event) => setRememberUsername(event.target.checked)} />아이디 기억하기</label>{error && <p className="error">{error}</p>}<button type="submit">로그인</button></form>}</section>
  </main>;
}

export default App;
