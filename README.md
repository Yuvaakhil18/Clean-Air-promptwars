# 🌬️ Clean Air Companion

> An intelligent, context-aware clean air advisor providing tailored daily routines, indoor air purification strategies, and low-emission commuting alternatives based on household vulnerability and ambient PM2.5 levels.

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-126%20passed-success.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-96.71%25-brightgreen.svg)](pytest.ini)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## 📌 1. Chosen Vertical

**Vertical:** **Public Health, Climate Resilience & Urban Environmental Safety**

Air pollution—specifically ambient and household fine particulate matter ($\text{PM}_{2.5}$)—is among the greatest environmental health risks worldwide. Standard air-quality applications merely display raw index numbers (AQI) or generic warnings ("unhealthy for everyone"). They fail to offer practical, actionable guidance tailored to household demographics (e.g., infants, pregnancy, asthma/COPD, elderly), home building physics (room volume, cooking fuels, CADR ratings), and commuting patterns.

**Clean Air Companion** bridges the gap between raw environmental sensors and everyday human decisions with transparent, explainable recommendations.

---

## 🧠 2. Approach and Logic

The architecture is built on a **defense-in-depth, deterministic-first logic model**:

```
                       ┌─────────────────────────┐
                       │   User Context Input    │
                       │ (Demographics, Air, Home)│
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ Pydantic Validation     │
                       │ (Strict, sanitized)     │
                       └────────────┬────────────┘
                                    │
            ┌───────────────────────┼────────────────────────┐
            ▼                       ▼                        ▼
┌───────────────────────┐ ┌───────────────────┐ ┌─────────────────────────┐
│ Air Quality Classifier│ │ Engineering Impact│ │ Rule-Based Action Matrix│
│ (US EPA & India NAQI) │ │ Physical Formulas │ │ (Vulnerability-tiered)  │
└───────────┬───────────┘ └─────────┬─────────┘ └────────────┬────────────┘
            │                       │                        │
            └───────────────────────┼────────────────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ Hybrid Narrative Engine │
                       │ (LLM with deterministic │
                       │    template fallback)   │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ Comprehensive AirPlan   │
                       └─────────────────────────┘
```

### Core Decision Logic
1. **Multi-Scale Risk Classification:** Translates $\text{PM}_{2.5}$ concentration ($\mu\text{g/m}^3$) into standard tiered severity levels using official cutoffs for either **US EPA AQI** or **India's CPCB NAQI**.
2. **Physical Engineering Impact Modeling:** Rather than generating vague suggestions, the system computes verifiable mathematical impacts:
   - **Purifier Steady-State Removal Rate:** Sized using room volume and clean air delivery rate (CADR):
     $$\text{Removal Share} = \frac{k}{\text{ACH} + k}, \quad k = \frac{\text{CADR}}{V}$$
   - **Indoor Infiltration PM2.5:** Estimates indoor particulate dose with open vs. closed envelope scenarios:
     $$\text{Indoor } \text{PM}_{2.5} = \text{Outdoor} \times P \times \frac{\text{ACH}}{\text{ACH} + k}$$
   - **Commute Carbon Offsets:** Models passenger-km emission differentials between driving, public transit, and active commuting.
3. **Vulnerability-Aware Rules:** Sensitivities (children, seniors, pregnancy, respiratory issues) dynamically inject specialized guidance (e.g., pediatric mask limitations, rescue inhaler protocols, avoiding outdoor exertion).
4. **Hybrid Narrative Layer:** Generates accessible guidance using Claude/LLM with strict prompt injection mitigation, with a deterministic fallback guaranteeing zero-downtime reliability.

---

## ⚙️ 3. How the Solution Works

1. **Frontend Interface:** A lightweight, accessible Single Page Application (SPA) designed with a clean editorial aesthetic, structured fieldsets, and responsive bento-box result tiles.
2. **Backend API (`FastAPI`):**
   - Serves the frontend at `/` with strict security headers (CSP, HSTS, Permissions-Policy).
   - Exposes `/api/advice` with strict Pydantic parsing and rate limiting.
3. **Execution Pipeline:**
   - Validates all form inputs (bounds, whitespace, and non-printable character stripping).
   - Computes physical impact metrics and safety warnings.
   - Summarizes personalized action items and outputs an atomic, structured `AirPlan`.

---

## 📐 4. Assumptions Made

- **Building Air Infiltration:** Assumes an air exchange rate ($\text{ACH}$) of $0.5\,\text{h}^{-1}$ for closed residential windows and $2.0\,\text{h}^{-1}$ for open windows.
- **Particulate Penetration Factor ($P$):** Assumed at $0.7$ (70% of outdoor $\text{PM}_{2.5}$ infiltrates typical closed residential building envelopes without active filtration).
- **Purifier Sizing Target:** Sized targeting an 80% steady-state particulate reduction.
- **Commuting Working Weeks:** Assumed at 46 working weeks per year.
- **Default Baseline:** If no $\text{PM}_{2.5}$ reading is supplied by the user, the assistant defaults to an unmeasured "Moderate" estimate and flags a warning advising localized monitoring.

---

## 🎯 5. Evaluation Focus Areas Alignment

### 🧹 Code Quality
- **Clean Architecture:** Strict separation of concerns (`models.py`, `airquality.py`, `advice.py`, `impact.py`, `narrative.py`, `planner.py`, `main.py`).
- **Standardized Typing:** Fully type-hinted with PEP 561 compliance ([app/py.typed](app/py.typed)).
- **Docstrings & Clean Lint:** Complete PEP 257 docstrings and passes `ruff check` with **0 errors**.

### 🔒 Security
- **Strict Content Security Policy (CSP):** `default-src 'self'` with no inline scripts or arbitrary remote scripts.
- **Rate Limiting:** Protects the inference endpoint against denial of service and cost spam via `slowapi` (30 req/min).
- **CORS Restricted:** Explicitly confined to localhost/127.0.0.1 origins.
- **Prompt Injection Defense:** Untrusted user inputs are XML-delimiter-escaped and quarantined within `<household>` tags under strict system instructions.
- **Credential Hygiene:** API key is scrubbed from logs and `repr()` using dataclass `repr=False`.

### ⚡ Efficiency
- Zero bulky frontend dependencies (vanilla JavaScript, pure modern CSS with CSS variables).
- Microsecond deterministic physical calculations.
- LLM is called strictly for the text narrative; all decision rules and physical formulas execute locally on the CPU.

### 🧪 Testing
- **126 automated test cases** across 9 test modules with **96.71% overall code coverage**.
- Enforced test thresholds in `pytest.ini` (`--cov-fail-under=85`).
- Covers boundary values, model validators, failure fallbacks, division guards, and security headers.

### ♿ Accessibility
- Built using semantic HTML5 (`<main>`, `<fieldset>`, `<legend>`, `<label>`, `<article>`).
- Live updates announced to assistive technology via `aria-live="polite"`.
- Visual meter paired with accessible screen-reader-only labels (`.sr-only`: *"Risk level X out of 5"*).
- Invalid form inputs flagged dynamically with `aria-invalid="true"`.
- Contrast exceeds WCAG AA guidelines.

### 🎯 Problem Statement Alignment
- Delivers an intelligent, practical, and usable dynamic companion that transforms passive data into proactive, household-specific air safety plans.

---

## 🚀 6. Getting Started

### Prerequisites
- Python 3.10+ (tested on Python 3.13)

### Installation
```bash
git clone <your-repo-url>
cd clean-air-companion

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration (Optional)
```bash
cp .env.example .env
# Edit .env to supply your ANTHROPIC_API_KEY (or leave blank to use the deterministic fallback)
```

### Running Locally
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

### Running Tests & Linting
```bash
# Run test suite with coverage
pytest

# Run linter
ruff check app tests
```
