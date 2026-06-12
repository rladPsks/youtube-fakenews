# 한국어 유튜브 허위정보 판별 시스템

## 프로젝트 소개

본 프로젝트는 대규모 언어모델(LLM)을 활용하여 한국어 유튜브 영상의 허위정보 여부를 판별하고, 통계적 신뢰성 검정을 통해 신뢰 가능한 경우에만 결과를 제공하는 웹 기반 시스템이다.

유튜브 영상의 자막을 자동으로 수집한 후 Qwen 모델을 이용해 허위정보 여부를 반복적으로 판단하며, FACTTEST와 Conformal Prediction 기반 방법론을 적용하여 결과의 신뢰성을 평가한다.

---

## 주요 기능

* 유튜브 URL 입력
* 자막 자동 수집
* Qwen 기반 허위정보 판별
* 7회 반복 추론(Multi-Sampling)
* Answer Entropy 계산
* TF-IDF 기반 판단 이유 유사도 계산
* FACTTEST Score 산출
* Conformal Prediction 기반 결과 수용/보류 판단
* 웹 기반 결과 시각화

---

## 시스템 구조

YouTube URL

↓

Transcript Extraction

↓

Qwen 3.5-4B Inference (7 Samples)

↓

Feature Extraction

* Answer Entropy
* Reason Similarity

↓

FACTTEST Score

↓

Conformal Prediction

↓

ACCEPT / ABSTAIN

↓

Web Interface

---

## 기술 스택

### Frontend

* React
* Vite

### Backend

* FastAPI
* Python

### AI Model

* Qwen 3.5-4B

### Machine Learning

* Scikit-Learn
* Gradient Boosting

### Deployment

* RunPod
* Vercel

---

## Repository Structure

frontend/

* React Frontend

backend/

* FastAPI Backend
* Qwen Inference
* FACTTEST Module

---

## Web Demo

https://youtube-fakenews.vercel.app

---

## 개발자

김예나

이화여자대학교
수학교육과 / 통계학과 / 소프트웨어 연계전공

2026 도전학기제 프로젝트
