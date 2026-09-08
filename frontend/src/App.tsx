import { FormEvent, useState } from "react";

import { createUser, login, User } from "./api/client";
import JobsPage from "./features/jobs/JobsPage";
import "./styles.css";

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await login(username, password);
      localStorage.setItem("jobda_access_token", result.access_token);
      setUser(result.user);
      setMessage(`${result.user.display_name}님, 로그인되었습니다.`);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "로그인에 실패했습니다.");
    }
  }

  async function handleCreateUser(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const createdUser = await createUser(username, password, displayName);
      setMessage(`${createdUser.username} 사용자를 생성했습니다.`);
      setUsername("");
      setPassword("");
      setDisplayName("");
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "사용자 생성에 실패했습니다.");
    }
  }

  if (user) {
    return <JobsPage user={user} onLogout={() => { localStorage.removeItem("jobda_access_token"); setUser(null); }} />;
  }

  return (
    <main className="shell">
      <section className="intro">
        <div className="eyebrow">PRIVATE JOB DASHBOARD</div>
        <h1>JOBDA</h1>
        <p>흩어진 채용공고를 한곳에서 확인하는 개인 대시보드</p>
      </section>
      <section className="panel">
        <div className="panel-heading">
          <span className="section-kicker">ACCESS</span>
          <h2>로그인</h2>
        </div>
        <form onSubmit={handleLogin}>
          <label>아이디<input value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
          <label>비밀번호<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
          <button type="submit">로그인</button>
        </form>
        <p className="hint">초기 관리자 계정은 서버 환경변수로 설정합니다.</p>
        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}
      </section>
      <section className="panel admin-panel">
        <div className="panel-heading">
          <span className="section-kicker">ADMIN</span>
          <h2>사용자 생성</h2>
        </div>
        <form onSubmit={handleCreateUser}>
          <label>표시 이름<input value={displayName} onChange={(event) => setDisplayName(event.target.value)} required /></label>
          <label>아이디<input value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
          <label>초기 비밀번호<input type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
          <button type="submit" className="secondary">관리자 로그인 후 생성</button>
        </form>
      </section>
    </main>
  );
}

export default App;
