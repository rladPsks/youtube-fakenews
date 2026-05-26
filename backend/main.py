from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pipeline import analyze_video
from fastapi import HTTPException

app = FastAPI(title="Korean YouTube Fake News Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str

@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        return analyze_video(req.url)

    except RuntimeError as e:
        code = str(e)

        if code.startswith("NO_TRANSCRIPT"):
            raise HTTPException(
                status_code=400,
                detail="이 영상은 사용할 수 있는 자막이 없습니다."
            )

        if code == "QWEN_TIMEOUT":
            raise HTTPException(
                status_code=408,
                detail="Qwen 분석 시간이 10분을 초과했습니다. 더 짧은 영상으로 다시 시도해주세요."
            )

        raise HTTPException(
            status_code=500,
            detail=f"분석 중 오류가 발생했습니다: {code}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"서버 오류가 발생했습니다: {repr(e)}"
        )