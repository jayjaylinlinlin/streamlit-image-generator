import streamlit as st
import google.genai as genai
from google.genai import types
from io import BytesIO
from PIL import Image
import base64
import re
import zipfile
import json
import time

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="이미지 생성기 - Vision Maker",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
/* Sidebar dark theme */
section[data-testid="stSidebar"] {
    background: #1a1b2e !important;
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] .stTextInput > div > div > input,
section[data-testid="stSidebar"] .stTextArea > div > div > textarea,
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stNumberInput > div > div > input {
    background: #252640 !important;
    border: 1px solid #3d3e5c !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
}

.sidebar-label {
    color: #a78bfa !important;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
    margin-top: 0.8rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Step cards */
.step-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 0.5rem;
}
.step-badge {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white !important;
    border-radius: 50%;
    width: 32px; height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.9rem;
    flex-shrink: 0;
}
.step-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1e293b;
}

/* Segment card */
.seg-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
}
.seg-num {
    display: inline-block;
    background: #6366f1;
    color: white !important;
    border-radius: 6px;
    padding: 1px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 8px;
}

/* Prompt block */
.prompt-block {
    background: #1e1f38;
    color: #e2e8f0 !important;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-family: monospace;
    font-size: 0.82rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
}
.prompt-num {
    color: #a78bfa !important;
    font-weight: 700;
}

/* Main header */
.main-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 0.3rem;
}
.main-header .icon-box {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 12px;
    width: 46px; height: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
}
.main-header h1 {
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0;
}
.main-header .ver {
    color: #6366f1;
    font-size: 0.85rem;
    font-weight: 600;
}
.main-header .sub {
    color: #64748b;
    font-size: 0.8rem;
    margin: 0;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: #94a3b8;
}
.empty-state .big-icon { font-size: 3.5rem; opacity: 0.4; margin-bottom: 0.8rem; }
.empty-state h3 { color: #64748b; font-size: 1rem; margin-bottom: 0.4rem; }
.empty-state p { font-size: 0.82rem; }

.block-container { padding-top: 1rem; }

/* Analysis card */
.analysis-card {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 8px;
}
.analysis-card h4 { color: #166534; margin: 0 0 8px 0; font-size: 0.95rem; }
.analysis-card p { color: #166534; font-size: 0.85rem; margin: 4px 0; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTS
# ============================================================================
NANO_BANANA_2_MODEL = "gemini-2.0-flash-exp"

DEFAULT_PROMPT_TEMPLATE = """Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [행동 및 아이콘 묘사 (영문) + no text/letters 강조]"""

DEFAULT_STYLE_GUIDE = """💎 Gems 시스템 지침 (System Instructions) - [Simple & Economic Focus Ver 7.0]
당신은 '2D 스틱맨 애니메이션 전문 프롬프트 디렉터'입니다.
사용자와의 상호작용은 철저하게 아래의 대화형 워크플로우를 따르며, 출력은 지정된 템플릿을 엄격히 준수합니다.

#### 🔄 대화형 작업 프로세스 (Interactive Workflow)

1단계: 대본 수신 및 질문 (Script Reception)
 트리거: 사용자가 [대본]만 입력했을 때.
 행동: 대본 확인 후, 반드시 컷당 시간(초)을 물어봅니다.
     예시: "대본을 확인했습니다. 한 컷당 몇 초 호흡으로 나눌까요? (예: 3초, 5초 등)"

2단계: 시간 적용 및 대본 분류 (Segmentation)
 트리거: 사용자가 [시간]을 입력했을 때.
 로직: 한국어 내레이션 기준 1초당 4~5글자(공백 포함)로 계산하여 번호를 매겨 분류합니다. (이 단계에서는 프롬프트 생성 X)
 출력: 번호가 매겨진 텍스트 리스트만 출력.

3단계: 이미지 프롬프트 생성 (Generation)
 트리거: 사용자가 분류된 리스트를 보고 "계속", "진행해"라고 했을 때.
 행동: 분류된 번호에 맞춰 [출력 템플릿]에 따라 영문 프롬프트를 작성합니다.
 형식: CSS 코드 블록 안에 순수 텍스트로 출력합니다.

---

#### 🎨 스타일 가이드 (Style Lock)

1. 비주얼 정의 (Visuals)
 캐릭터: Pure-white round faces, single hard cel shading(턱 아래 1단 그림자), thick black outline, thicker torso and neck, stick limbs, flat matte colors.
 배경: 저채도 평면 블록(Low saturation flat blocks), 글자 절대 금지.
 네거티브(내재): 3D, photoreal, gradient, soft light, text, letters, speech bubble.

2. 장면 해석 (Scene Interpretation)
 행동 중심: 감정은 눈썹/입선으로, 동작은 명확한 동사(leans, points, nods, clasps, gestures)로 표현.
 경제 개념 시각화: 추상적 개념은 인물+아이콘/도형으로 변환.
     상승/하락 → 화살표 아이콘(Arrow icons)
     데이터/실적 → 차트 도형, 기어, 지도 핀 (Chart shapes, Gears, Map pins)
     계약/문서 → 빈 종이 아이콘 (Blank paper icons)
     주의: 모든 간판, 화면, 문서에 글자(Text) 대신 기호/도형만 사용.

---

#### 📝 출력 템플릿 (Output Template)
모든 프롬프트는 반드시 아래 문장으로 시작해야 합니다. 대괄호 `[...]` 부분만 장면에 맞춰 영문으로 작성하세요.

> Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [행동 및 아이콘 묘사 (영문) + no text/letters 강조]"""

LANGUAGE_CONFIG = {
    "Korean": {"chars_per_second": 4.5, "label": "한국어"},
    "Japanese": {"chars_per_second": 4.0, "label": "日本語"},
    "English": {"chars_per_second": 3.0, "label": "English"},
    "Thai": {"chars_per_second": 4.0, "label": "ไทย"},
    "Chinese": {"chars_per_second": 3.5, "label": "中文"},
}

# ============================================================================
# SESSION STATE
# ============================================================================
defaults = {
    "api_key": "",
    "script_text": "",
    "cut_seconds": 4,
    "selected_language": "Korean",
    "prompt_template": DEFAULT_PROMPT_TEMPLATE,
    "style_guide": DEFAULT_STYLE_GUIDE,
    # Step results
    "step1_analysis": None,
    "step2_segments": [],
    "step3_prompts": [],
    "step4_images": [],
    "current_step": 0,
    "is_running": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def get_client():
    if not st.session_state.api_key:
        st.error("사이드바에서 API Key를 입력해주세요.")
        return None
    return genai.Client(api_key=st.session_state.api_key)


# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    # API Key
    st.markdown('<div class="sidebar-label">🔑 Gemini API Key</div>', unsafe_allow_html=True)
    api_key_input = st.text_input(
        "API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="Gemini API Key를 입력하세요",
        label_visibility="collapsed",
    )
    st.session_state.api_key = api_key_input

    st.divider()

    # Cut duration (seconds)
    st.markdown('<div class="sidebar-label">⏱️ 컷당 시간 (초)</div>', unsafe_allow_html=True)
    cut_seconds = st.number_input(
        "cut_sec",
        min_value=1,
        max_value=30,
        value=st.session_state.cut_seconds,
        step=1,
        label_visibility="collapsed",
    )
    st.session_state.cut_seconds = cut_seconds

    # Language
    st.markdown('<div class="sidebar-label">🌐 대본 언어</div>', unsafe_allow_html=True)
    selected_language = st.selectbox(
        "lang",
        options=list(LANGUAGE_CONFIG.keys()),
        format_func=lambda x: LANGUAGE_CONFIG[x]["label"],
        index=list(LANGUAGE_CONFIG.keys()).index(st.session_state.selected_language),
        label_visibility="collapsed",
    )
    st.session_state.selected_language = selected_language

    cps = LANGUAGE_CONFIG[selected_language]["chars_per_second"]
    chars_per_cut = int(cut_seconds * cps)
    st.caption(f"컷당 약 {chars_per_cut}글자 (공백 포함)")

    st.divider()

    # Prompt template
    st.markdown('<div class="sidebar-label">🖼️ 이미지 프롬프트 형식</div>', unsafe_allow_html=True)
    prompt_template = st.text_area(
        "tmpl",
        value=st.session_state.prompt_template,
        height=120,
        label_visibility="collapsed",
        help="이미지 생성 프롬프트의 형식을 정의합니다. [...]  부분이 장면 설명으로 교체됩니다.",
    )
    st.session_state.prompt_template = prompt_template

    st.divider()

    # Style guide
    st.markdown('<div class="sidebar-label">🎨 스타일 가이드</div>', unsafe_allow_html=True)
    with st.expander("스타일 가이드 편집", expanded=False):
        style_guide = st.text_area(
            "guide",
            value=st.session_state.style_guide,
            height=400,
            label_visibility="collapsed",
        )
        st.session_state.style_guide = style_guide

    st.divider()

    # Model info
    st.markdown('<div class="sidebar-label">📦 생성 모델</div>', unsafe_allow_html=True)
    st.caption(f"🔥 Nano Banana 2 (나노바나나2)")
    st.caption(f"Model: {NANO_BANANA_2_MODEL}")

    # Reset button
    st.divider()
    if st.button("🔄 전체 초기화", use_container_width=True):
        for k in ["step1_analysis", "step2_segments", "step3_prompts", "step4_images", "current_step", "is_running"]:
            st.session_state[k] = defaults[k]
        st.rerun()


# ============================================================================
# CORE FUNCTIONS
# ============================================================================
def split_script_by_seconds(script, cut_sec, chars_per_sec):
    """Split script into segments based on seconds and character count."""
    chars_per_cut = int(cut_sec * chars_per_sec)
    text = script.strip()
    if not text:
        return []

    # Split by sentences first
    sentences = re.split(r'(?<=[.!?\u3002\uff01\uff1f])\s*', text)
    segments = []
    current = ""

    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(current) + len(s) + 1 <= chars_per_cut:
            current = (current + " " + s).strip() if current else s
        else:
            if current:
                segments.append(current)
            # If single sentence is longer than cut, split by chars
            while len(s) > chars_per_cut:
                segments.append(s[:chars_per_cut])
                s = s[chars_per_cut:]
            current = s

    if current:
        segments.append(current)

    return segments


def analyze_script(client, script):
    """Step 1: Analyze script content."""
    prompt = f"""다음 대본을 분석해주세요. JSON 형식으로 응답하세요.

대본:
{script}

응답 형식:
{{
  "topic": "주제 요약 (1줄)",
  "tone": "톤/분위기",
  "keywords": ["핵심 키워드1", "핵심 키워드2", "핵심 키워드3"],
  "total_chars": 총 글자수(숫자),
  "estimated_duration": "예상 내레이션 시간",
  "scene_count_suggestion": "권장 장면 수",
  "summary": "전체 내용 요약 (2-3줄)"
}}

JSON만 응답하세요."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = response.text.strip()
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        return json.loads(m.group())
    return {"topic": "분석 완료", "summary": text}


def generate_image_prompts(client, segments, style_guide, prompt_template):
    """Step 3: Generate image prompts for each segment."""
    all_segments_text = "\n".join([f"{i+1}. {seg}" for i, seg in enumerate(segments)])

    prompt = f"""{style_guide}

아래 분류된 대본 세그먼트 각각에 대해 이미지 프롬프트를 생성하세요.

프롬프트 형식:
{prompt_template}

분류된 세그먼트:
{all_segments_text}

각 세그먼트에 대해 위 형식을 따르는 영문 이미지 프롬프트를 생성하세요.
[...] 부분을 장면에 맞는 영문 설명으로 교체하세요.
반드시 각 프롬프트를 큰따옴표로 감싸고, 한 줄에 하나씩 출력하세요.
총 {len(segments)}개의 프롬프트를 생성하세요."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    text = response.text.strip()
    # Extract prompts between quotes
    prompts = re.findall(r'"([^"]+)"', text)

    # If regex didn't find enough, try line-by-line
    if len(prompts) < len(segments):
        lines = [l.strip().strip('"').strip("'") for l in text.split("\n") if l.strip() and "Upgraded" in l]
        if len(lines) >= len(segments):
            prompts = lines

    return prompts


def generate_single_image(client, prompt, idx):
    """Step 4: Generate a single image from prompt."""
    response = client.models.generate_content(
        model=NANO_BANANA_2_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data))
                return img
    return None


# ============================================================================
# MAIN - Header
# ============================================================================
st.markdown("""
<div class="main-header">
    <div class="icon-box">🎬</div>
    <div>
        <h1 style="display:inline">이미지 생성기</h1>
        <span class="ver">Vision Maker</span>
        <p class="sub">대본을 넣으면 AI가 자동으로 이미지를 생성합니다. (나노바나나2)</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ============================================================================
# SCRIPT INPUT
# ============================================================================
script_text = st.text_area(
    "📝 대본 입력",
    value=st.session_state.script_text,
    height=200,
    placeholder="여기에 대본을 붙여넣으세요...\n\n예시: 부자들은 위기를 기회로 삼습니다. 주식 시장이 폭락할 때 오히려 매수 버튼을 누르죠.",
)
st.session_state.script_text = script_text

# Generate button
generate_btn = st.button(
    "🚀 생성 시작 (4단계 자동 실행)",
    use_container_width=True,
    type="primary",
    disabled=st.session_state.is_running,
)

st.divider()

# ============================================================================
# 4-STEP PIPELINE
# ============================================================================
if generate_btn and script_text.strip():
    client = get_client()
    if client:
        st.session_state.is_running = True
        st.session_state.step1_analysis = None
        st.session_state.step2_segments = []
        st.session_state.step3_prompts = []
        st.session_state.step4_images = []

        # ── STEP 1: 대본 분석 ──
        st.session_state.current_step = 1
        step1_container = st.container()
        with step1_container:
            st.markdown('<div class="step-header"><div class="step-badge">1</div><div class="step-title">대본 분석</div></div>', unsafe_allow_html=True)
            with st.spinner("대본을 분석하고 있습니다..."):
                try:
                    analysis = analyze_script(client, script_text.strip())
                    st.session_state.step1_analysis = analysis
                    st.success("대본 분석 완료!")
                except Exception as e:
                    st.error(f"분석 오류: {str(e)}")
                    st.session_state.is_running = False
                    st.stop()

        # ── STEP 2: 초단위 분할 ──
        st.session_state.current_step = 2
        step2_container = st.container()
        with step2_container:
            st.markdown('<div class="step-header"><div class="step-badge">2</div><div class="step-title">초단위 분할</div></div>', unsafe_allow_html=True)
            cps = LANGUAGE_CONFIG[st.session_state.selected_language]["chars_per_second"]
            segments = split_script_by_seconds(
                script_text.strip(),
                st.session_state.cut_seconds,
                cps,
            )
            st.session_state.step2_segments = segments
            st.success(f"{st.session_state.cut_seconds}초 단위로 {len(segments)}개 세그먼트로 분할 완료!")

        # ── STEP 3: 이미지 프롬프트화 ──
        st.session_state.current_step = 3
        step3_container = st.container()
        with step3_container:
            st.markdown('<div class="step-header"><div class="step-badge">3</div><div class="step-title">이미지 프롬프트 생성</div></div>', unsafe_allow_html=True)
            with st.spinner("프롬프트를 생성하고 있습니다..."):
                try:
                    prompts = generate_image_prompts(
                        client,
                        segments,
                        st.session_state.style_guide,
                        st.session_state.prompt_template,
                    )
                    st.session_state.step3_prompts = prompts
                    st.success(f"{len(prompts)}개 이미지 프롬프트 생성 완료!")
                except Exception as e:
                    st.error(f"프롬프트 생성 오류: {str(e)}")
                    st.session_state.is_running = False
                    st.stop()

        # ── STEP 4: 이미지 생성 ──
        st.session_state.current_step = 4
        step4_container = st.container()
        with step4_container:
            st.markdown('<div class="step-header"><div class="step-badge">4</div><div class="step-title">이미지 생성 (나노바나나2)</div></div>', unsafe_allow_html=True)
            images = []
            total = len(st.session_state.step3_prompts)
            progress = st.progress(0, text=f"이미지 생성 중... (0/{total})")

            for idx, prompt in enumerate(st.session_state.step3_prompts):
                progress.progress((idx) / total, text=f"이미지 생성 중... ({idx+1}/{total})")
                try:
                    img = generate_single_image(client, prompt, idx)
                    if img:
                        seg_text = segments[idx] if idx < len(segments) else ""
                        images.append({
                            "image": img,
                            "prompt": prompt,
                            "segment": seg_text,
                            "index": idx + 1,
                        })
                    else:
                        st.warning(f"이미지 {idx+1}: 생성 결과 없음")
                except Exception as e:
                    st.warning(f"이미지 {idx+1} 실패: {str(e)}")
                    time.sleep(1)

            progress.progress(1.0, text="이미지 생성 완료!")
            st.session_state.step4_images = images
            st.success(f"총 {len(images)}개 이미지 생성 완료!")

        st.session_state.is_running = False
        st.session_state.current_step = 5
        st.rerun()

elif generate_btn and not script_text.strip():
    st.error("대본을 입력해주세요.")

# ============================================================================
# DISPLAY RESULTS (after pipeline completes)
# ============================================================================

# ── STEP 1 결과: 대본 분석 ──
if st.session_state.step1_analysis:
    st.markdown('<div class="step-header"><div class="step-badge">1</div><div class="step-title">대본 분석</div></div>', unsafe_allow_html=True)
    analysis = st.session_state.step1_analysis

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**📌 주제:** {analysis.get('topic', '-')}")
        st.markdown(f"**🎭 톤:** {analysis.get('tone', '-')}")
    with col2:
        st.markdown(f"**📊 글자수:** {analysis.get('total_chars', '-')}")
        st.markdown(f"**⏱️ 예상 시간:** {analysis.get('estimated_duration', '-')}")
    with col3:
        keywords = analysis.get('keywords', [])
        if keywords:
            st.markdown(f"**🔑 키워드:** {', '.join(keywords)}")
        st.markdown(f"**🎬 권장 장면수:** {analysis.get('scene_count_suggestion', '-')}")

    if analysis.get('summary'):
        st.info(f"**요약:** {analysis['summary']}")

    st.divider()

# ── STEP 2 결과: 초단위 분할 ──
if st.session_state.step2_segments:
    st.markdown('<div class="step-header"><div class="step-badge">2</div><div class="step-title">초단위 분할 결과</div></div>', unsafe_allow_html=True)
    st.caption(f"{st.session_state.cut_seconds}초 단위 | {len(st.session_state.step2_segments)}개 세그먼트")

    for i, seg in enumerate(st.session_state.step2_segments):
        st.markdown(f'<div class="seg-card"><span class="seg-num">{i+1}</span>{seg}</div>', unsafe_allow_html=True)

    st.divider()

# ── STEP 3 결과: 이미지 프롬프트 ──
if st.session_state.step3_prompts:
    st.markdown('<div class="step-header"><div class="step-badge">3</div><div class="step-title">이미지 프롬프트</div></div>', unsafe_allow_html=True)
    st.caption(f"{len(st.session_state.step3_prompts)}개 프롬프트 생성됨")

    for i, prompt in enumerate(st.session_state.step3_prompts):
        st.markdown(f'<div class="prompt-block"><span class="prompt-num">[{i+1}]</span> {prompt}</div>', unsafe_allow_html=True)

    st.divider()

# ── STEP 4 결과: 생성된 이미지 ──
if st.session_state.step4_images:
    st.markdown('<div class="step-header"><div class="step-badge">4</div><div class="step-title">생성된 이미지</div></div>', unsafe_allow_html=True)
    st.caption(f"총 {len(st.session_state.step4_images)}개 이미지")

    cols = st.columns(3)
    for i, d in enumerate(st.session_state.step4_images):
        with cols[i % 3]:
            st.image(d["image"], use_container_width=True)
            st.caption(f"**#{d['index']}**")
            seg = d.get("segment", "")
            if seg:
                st.text(seg[:80] + "..." if len(seg) > 80 else seg)

    st.divider()

    # Download section
    st.subheader("📥 다운로드")

    dl_cols = st.columns(min(len(st.session_state.step4_images), 4))
    for i, d in enumerate(st.session_state.step4_images):
        with dl_cols[i % len(dl_cols)]:
            buf = BytesIO()
            d["image"].save(buf, format="PNG")
            buf.seek(0)
            st.download_button(
                f"이미지 {d['index']}",
                buf.getvalue(),
                f"image_{d['index']}.png",
                "image/png",
                key=f"dl_{i}",
            )

    # ZIP download
    zbuf = BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, d in enumerate(st.session_state.step4_images):
            buf = BytesIO()
            d["image"].save(buf, format="PNG")
            buf.seek(0)
            zf.writestr(f"image_{d['index']}.png", buf.getvalue())
    zbuf.seek(0)
    st.download_button(
        "📦 전체 다운로드 (ZIP)",
        zbuf.getvalue(),
        "generated_images.zip",
        "application/zip",
        key="dl_zip",
        use_container_width=True,
    )

# ============================================================================
# EMPTY STATE
# ============================================================================
if not any([
    st.session_state.step1_analysis,
    st.session_state.step2_segments,
    st.session_state.step3_prompts,
    st.session_state.step4_images,
]):
    st.markdown("""
    <div class="empty-state">
        <div class="big-icon">🖼️</div>
        <h3>대본을 넣고 생성을 시작하세요</h3>
        <p>대본 입력 → 대본 분석 → 초단위 분할 → 프롬프트 생성 → 이미지 생성</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.caption(f"이미지 생성기 | Powered by Gemini API (나노바나나2) | {LANGUAGE_CONFIG[st.session_state.selected_language]['label']}")
