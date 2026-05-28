import { useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL;

function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const analyzeVideo = async () => {
    if (!url.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        let message = "분석 요청 실패";

        try {
          const errorData = await response.json();
          message = errorData.detail || message;
        } catch {
          message = "서버 응답을 읽을 수 없습니다.";
        }

        throw new Error(message);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      alert(err.message || "분석 실패: backend 서버 또는 URL을 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  const predictionClass = result?.prediction === "REAL" ? "real" : "fake";

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand-icon">✓</div>
        <div>
          <h1>FactGuard</h1>
          <p>Korean YouTube Fake News Detector</p>
        </div>
      </header>

      <main className="page">
        <section className="input-card">
          <h2>▶ YouTube 영상 분석</h2>

          <div className="input-row">
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="YouTube URL을 입력하세요..."
            />
            <button onClick={analyzeVideo} disabled={loading || !url.trim()}>
              {loading ? "분석 중..." : "분석하기"}
            </button>
          </div>
        </section>

        {!result && !loading && (
          <section className="empty-state">
            <div className="shield">🛡</div>
            <h2>영상을 분석해보세요</h2>
            <p>
              YouTube URL을 입력하면 Qwen LLM이 7회 판단하고, FACTTEST 기반
              신뢰성 검정으로 답변 여부를 결정합니다.
            </p>
          </section>
        )}

        {loading && (
          <section className="empty-state">
            <div className="loader" />
            <h2>분석 중입니다</h2>
            <p>
              자막 추출, Qwen 7회 추론, Gradient Boosting FACTTEST를 수행하고
              있습니다.
            </p>
          </section>
        )}

        {result && (
          <section className="results">
            <div className={`prediction-card ${predictionClass}`}>
              <div className="prediction-left">
                <div className="prediction-icon">
                  {result.prediction === "REAL" ? "✓" : "!"}
                </div>
                <div>
                  <p className="small-label">최종 예측</p>
                  <h2>{result.prediction}</h2>
                  <p className="muted">
                    {result.prediction === "REAL"
                      ? "이 영상은 사실 기반 콘텐츠로 판단됩니다."
                      : "이 영상은 허위 정보 가능성이 높습니다."}
                  </p>
                </div>
              </div>

              <div className="prediction-right">
                <p className="small-label">Video ID</p>
                <strong>{result.video_id}</strong>
              </div>
            </div>

            <div className="reason-card">
              <p className="small-label">대표 판단 이유</p>
              <p>{result.representative_reason}</p>
            </div>

            <div className="metric-grid">
              <Metric title="p0" value={result.p0} />
              <Metric title="p1" value={result.p1} />
              <Metric title="confidence" value={result.confidence} />
              <Metric title="entropy" value={result.entropy} />
              <Metric
                title="FACTTEST score"
                value={result.facttest_features?.facttest_score}
              />
            </div>

            <div className="feature-card">
              <h3>FACTTEST Features</h3>
              <div className="metric-grid three">
                <Metric
                  title="answer_entropy"
                  value={result.facttest_features?.answer_entropy}
                />
                <Metric
                  title="tfidf_reason_mean"
                  value={result.facttest_features?.tfidf_reason_mean}
                />
                <Metric
                  title="facttest_score"
                  value={result.facttest_features?.facttest_score}
                />
              </div>
            </div>

            <div className="facttest-card">
              <h3>Alpha별 FACTTEST 결과</h3>
              <div className="alpha-grid">
                {result.facttest.map((item) => (
                  <div className="alpha-card" key={item.alpha}>
                    <div className="alpha-top">
                      <span>α = {item.alpha}</span>
                      <span
                        className={
                          item.decision === "ACCEPT"
                            ? "badge accept"
                            : "badge abstain"
                        }
                      >
                        {item.decision}
                      </span>
                    </div>

                    <div className="score-line">
                      <p>score</p>
                      <strong>{item.score}</strong>
                    </div>

                    <div className="bar-bg">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${Math.min(item.score * 100, 100)}%`,
                        }}
                      />
                    </div>

                    <p className="tau">tau: {item.tau}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="reason-list-card">
              <button
                className="accordion-btn"
                onClick={() => setExpanded(!expanded)}
              >
                Qwen 7회 reasoning 보기 {expanded ? "▲" : "▼"}
              </button>

              {expanded && (
                <ol className="reason-list">
                  {result.all_outputs.map((item, idx) => (
                    <li key={idx}>
                      <span className="reason-index">{idx + 1}</span>
                      <div>
                        <strong>{item.label_name}</strong>
                        <p>{item.reason}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            <p className="disclaimer">
              ⚠️ 이 분석 결과는 AI 기반 자동 판별 시스템에 의해 생성되었습니다.
              최종 판단에는 추가 확인이 필요합니다.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}

function Metric({ title, value }) {
  return (
    <div className="metric">
      <p>{title}</p>
      <strong>{value ?? "-"}</strong>
    </div>
  );
}

export default App;
