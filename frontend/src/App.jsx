import { useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL;

const alphaOptions = [
  {
    label: "표준",
    value: 0.2,
    description: "더 많은 답변을 제공하는 기본 기준입니다.",
  },
  {
    label: "엄격",
    value: 0.15,
    description: "신뢰성과 답변 제공률의 균형을 맞춥니다.",
  },
  {
    label: "매우 엄격",
    value: 0.05,
    description: "매우 확실한 경우에만 답변을 제공합니다.",
  },
];

function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [showPrediction, setShowPrediction] = useState(false);
  const [showTechInfo, setShowTechInfo] = useState(false);
  const [selectedAlpha, setSelectedAlpha] = useState(0.2);

  const analyzeVideo = async () => {
    if (!url.trim()) return;

    setLoading(true);
    setResult(null);
    setExpanded(false);
    setShowPrediction(false);
    setShowTechInfo(false);
    setSelectedAlpha(0.2);

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
      setExpanded(false);
      setShowPrediction(false);
      setShowTechInfo(false);
    } catch (err) {
      alert(err.message || "분석 실패: backend 서버 또는 URL을 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  const selectedOption =
    alphaOptions.find((option) => option.value === selectedAlpha) ||
    alphaOptions[0];

  const primaryFacttest =
    result?.facttest?.find((item) => Number(item.alpha) === selectedAlpha) ||
    result?.facttest?.[0];

  const isAccepted = primaryFacttest?.decision === "ACCEPT";
  const predictionClass = result?.prediction === "REAL" ? "real" : "fake";

  const userDecisionText = isAccepted ? "결과 제공 가능" : "결과 제공 보류";

  const userDecisionDescription = isAccepted
    ? "선택한 기준에서 AI의 최종 예측을 제공해도 된다고 판단했습니다."
    : "선택한 기준에서 AI의 최종 예측을 바로 제공하기 어렵다고 판단했습니다.";

  const predictionText =
    result?.prediction === "REAL" ? "사실 기반 가능성 높음" : "허위 정보 가능성 높음";

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand-icon">✓</div>
        <div>
          <h1>한국어 유튜브 허위정보 판별 시스템</h1>
          <p>AI 기반 허위정보 탐지 및 신뢰성 검정</p>
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
              YouTube URL을 입력하면 AI가 여러 번 판단하고, 신뢰도 기준을 적용해
              결과 제공 여부를 먼저 결정합니다.
            </p>
          </section>
        )}

        {loading && (
          <section className="empty-state">
            <div className="loader" />
            <h2>분석 중입니다</h2>
            <p>자막 추출, AI 반복 판단, 신뢰도 검정을 수행하고 있습니다.</p>
          </section>
        )}

        {result && (
          <section className="results">
            <div className="feature-card">
              <h3 className="section-title">답변 제공 기준 선택</h3>
              <div className="alpha-grid three-options">
                {alphaOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    className={
                      selectedAlpha === option.value
                        ? "alpha-card selected"
                        : "alpha-card"
                    }
                    onClick={() => {
                      setSelectedAlpha(option.value);
                      setShowPrediction(false);
                      setExpanded(false);
                      setShowTechInfo(false);
                    }}
                  >
                    <div className="alpha-top">
                      <span>{option.label}</span>
                    </div>
                    <p className="muted">{option.description}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className={`prediction-card ${isAccepted ? "real" : "fake"}`}>
              <div className="prediction-left">
                <div className="prediction-icon">{isAccepted ? "✓" : "!"}</div>
                <div>
                  <h3 className="section-title">AI 결과 제공 여부</h3>
                  <h2>{userDecisionText}</h2>
                  <p className="muted">{userDecisionDescription}</p>
                </div>
              </div>

              <div className="prediction-right">
                <p className="result-side-label">선택한 기준</p>
                <strong>{selectedOption.label}</strong>
              </div>
            </div>

            {!isAccepted && (
              <div className="reason-card">
                <h3 className="section-title">결과 제공 보류 안내</h3>
                <p>
                  이 영상은 현재 선택한 기준에서 AI의 최종 예측을 바로 신뢰하기
                  어렵다고 판단되어 결과 공개를 보류합니다. 아래에서 AI가 여러 번
                  판단한 상세 이유는 확인할 수 있습니다.
                </p>
              </div>
            )}

            {isAccepted && !showPrediction && (
              <div className="reason-card">
                <h3 className="section-title">다음 단계</h3>
                <p>
                  선택한 기준에서 AI의 최종 예측을 제공할 수 있다고 판단했습니다.
                  아래 버튼을 누르면 최종 예측 결과를 확인할 수 있습니다.
                </p>
                <button
                  className="accordion-btn"
                  onClick={() => setShowPrediction(true)}
                >
                  AI 예측 결과 보기
                </button>
              </div>
            )}

            {isAccepted && showPrediction && (
              <>
                <div className={`prediction-card ${predictionClass}`}>
                  <div className="prediction-left">
                    <div className="prediction-icon">
                      {result.prediction === "REAL" ? "✓" : "!"}
                    </div>
                    <div>
                      <h3 className="section-title">AI 최종 예측</h3>
                      <h2>{predictionText}</h2>
                      <p className="muted">
                        {result.prediction === "REAL"
                          ? "이 영상은 사실 기반 콘텐츠일 가능성이 높다고 판단했습니다."
                          : "이 영상은 허위 정보일 가능성이 높다고 판단했습니다."}
                      </p>
                    </div>
                  </div>

                  <div className="prediction-right">
                    <p className="result-side-label">Video ID</p>
                    <strong>{result.video_id}</strong>
                  </div>
                </div>

                <div className="reason-card">
                  <h3 className="section-title">대표 판단 이유</h3>
                  <p>{result.representative_reason}</p>
                </div>

                <div className="metric-grid public-metrics">
                  <Metric title="허위 가능성 비율" value={result.p0} />
                  <Metric title="사실 기반 비율" value={result.p1} />
                  <Metric title="AI 판단 신뢰도" value={result.confidence} />
                </div>
              </>
            )}

            <div className="reason-list-card">
              <button
                className="accordion-btn"
                onClick={() => setExpanded(!expanded)}
              >
                AI가 7번 판단한 상세 이유 보기 {expanded ? "▲" : "▼"}
              </button>

              {expanded && (
                <ol className="reason-list">
                  {result.all_outputs.map((item, idx) => (
                    <li key={idx}>
                      <span className="reason-index">{idx + 1}</span>
                      <div>
                        <strong>
                          {item.label_name === "REAL"
                            ? "사실 기반"
                            : item.label_name === "FAKE"
                            ? "허위 가능성"
                            : item.label_name}
                        </strong>
                        <p>{item.reason}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            <div className="feature-card">
              <button
                className="accordion-btn"
                onClick={() => setShowTechInfo(!showTechInfo)}
              >
                상세 기술 정보 보기 {showTechInfo ? "▲" : "▼"}
              </button>

              {showTechInfo && (
                <>
                  <div className="metric-grid three tech-metrics">
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

                  <div className="facttest-card nested">
                    <h3>기준별 내부 검정 결과</h3>
                    <div className="alpha-grid">
                      {result.facttest.map((item) => (
                        <div className="alpha-card" key={item.alpha}>
                          <div className="alpha-top">
                            <span>alpha = {item.alpha}</span>
                            <span
                              className={
                                item.decision === "ACCEPT"
                                  ? "badge accept"
                                  : "badge abstain"
                              }
                            >
                              {item.decision === "ACCEPT" ? "수용" : "보류"}
                            </span>
                          </div>

                          <div className="score-line">
                            <p>score</p>
                            <strong>{item.score}</strong>
                          </div>

                          <p className="tau">tau: {item.tau}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
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
