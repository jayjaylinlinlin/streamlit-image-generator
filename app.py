import streamlit as st
import google.genai as genai
from google.genai import types
from io import BytesIO
from PIL import Image
import base64
import re
import zipfile

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(page_title="이미지 생성기", layout="wide", initial_sidebar_state="expanded")

# ============================================================================
# CONSTANTS & DEFAULTS
# ============================================================================
DEFAULT_PROMPT_TEMPLATE = """Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [행동 및 아이콘 묘사 + no text/letters 강조]"""

DEFAULT_STYLE_GUIDE = """💎 Gems 시스템 지침 (System Instructions) - [Simple & Economic Focus Ver 7.0]

당신은 '2D 스틱맨 애니메이션 전문 프롬프트 디렉터'입니다.
사용자와의 상호작용은 철저하게 아래의 대화형 워크플로우를 따르며, 출력은 지정된 템플릿을 엄격히 준수합니다.

#### 🔄 대화형 작업 프로세스 (Interactive Workflow)

1단계: 대본 수신 및 질문 (Script Reception)
 트리거: 사용자가 [대본]만 입력했을 때.
 행동: 대본 확인 후, 반드시 컷당 시간(초)을 물어봅니다.

2단계: 시간 적용 및 대본 분류 (Segmentation)
 트리거: 사용자가 [시간]을 입력했을 때.
 로직: 내레이션 기준으로 계산하여 번호를 매겨 분류합니다. (이 단계에서는 프롬프트 생성 X)
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

# 언어별 초당 글자 수 설정
LANGUAGE_CONFIG = {
    "한국어": {"chars_per_second": 4.5, "label": "🇰🇷 한국어"},
    "日本語": {"chars_per_second": 4.0, "label": "🇯🇵 日本語"},
    "English": {"chars_per_second": 3.0, "label": "🇺🇸 English"},
    "ไทย": {"chars_per_second": 4.0, "label": "🇹🇭 ไทย"},
    "中文": {"chars_per_second": 3.5, "label": "🇨🇳 中文"},
}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "script_text" not in st.session_state:
    st.session_state.script_text = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "segments" not in st.session_state:
    st.session_state.segments = []
if "image_prompts" not in st.session_state:
    st.session_state.image_prompts = []
if "generated_images" not in st.session_state:
    st.session_state.generated_images = []
if "current_step" not in st.session_state:
    st.session_state.current_step = 1

# ============================================================================
# SIDEBAR CONFIG
# ============================================================================
with st.sidebar:
    st.title("⚙️ 설정")

    api_key_input = st.text_input(
        "🔑 Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Google Gemini API 키를 입력하세요",
    )
    st.session_state.api_key = api_key_input

    st.divider()

    # 언어 선택
    language_options = list(LANGUAGE_CONFIG.keys())
    language_labels = [LANGUAGE_CONFIG[k]["label"] for k in language_options]
    selected_language = st.selectbox(
        "🌐 대본 언어",
        options=language_options,
        format_func=lambda x: LANGUAGE_CONFIG[x]["label"],
        help="대본의 언어를 선택하세요. 언어에 따라 초당 글자 수가 자동 조정됩니다.",
    )

    # 컷당 시간 슬라이더 (5~30초, 5초 단위)
    cut_duration = st.select_slider(
        "⏱️ 컷당 시간 (초)",
        options=[5, 10, 15, 20, 25, 30],
        value=5,
        help="한 컷을 재생할 시간 (초). 5초 단위로 조절 가능",
    )

    chars_per_second = LANGUAGE_CONFIG[selected_language]["chars_per_second"]
    chars_per_cut = int(cut_duration * chars_per_second)
    st.info(f"📏 {selected_language} 기준: 초당 {chars_per_second}글자 → 컷당 약 {chars_per_cut}글자")

    st.divider()

    st.subheader("📋 이미지 프롬프트 형식")
    prompt_template = st.text_area(
        "프롬프트 템플릿",
        value=DEFAULT_PROMPT_TEMPLATE,
        height=120,
        help="[...] 부분을 실제 장면 묘사로 대체하여 사용됩니다",
    )

    st.divider()

    st.subheader("🎨 스타일 가이드")
    style_guide = st.text_area(
        "스타일 가이드 (편집 가능)",
        value=DEFAULT_STYLE_GUIDE,
        height=300,
        help="이미지 프롬프트 생성 시 참고할 스타일 가이드입니다. 자유롭게 수정하세요.",
    )

# ============================================================================
# HELPER: Gemini Client
# ============================================================================
def get_client():
    """API 키로 Gemini 클라이언트를 생성합니다."""
    if not st.session_state.api_key:
        st.error("❌ 사이드바에서 API 키를 입력하세요.")
        return None
    return genai.Client(api_key=st.session_state.api_key)

# ============================================================================
# MAIN AREA - TITLE
# ============================================================================
st.title("🎬 Streamlit 이미지 생성기")
st.markdown("대본을 입력하고 Gemini API (Nano Banana 2)로 스틱맨 애니메이션 이미지를 자동 생성합니다.")

# ============================================================================
# STEP 1: SCRIPT ANALYSIS
# ============================================================================
st.header("📝 Step 1: 대본 분석")

script_input = st.text_area(
    "대본 입력",
    value=st.session_state.script_text,
    height=150,
    placeholder="여기에 대본을 입력하세요...",
    help="분석할 대본을 입력하면 핵심 장면과 감정을 자동으로 분석합니다",
)
st.session_state.script_text = script_input

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 대본 분석 시작", key="analyze_btn"):
        client = get_client()
        if client and script_input.strip():
            try:
                with st.spinner("🤖 대본 분석 중..."):
                    analysis_prompt = f"""다음 대본을 분석하고, 각 장면의 핵심 감정, 동작, 시각적 요소를 정리해주세요.
{selected_language}로 간결하게 분석 결과를 정리하세요:

대본:
{script_input}

분석 항목:
1. 핵심 감정/톤
2. 주요 동작들
3. 필요한 시각 요소들
4. 장면 전환 포인트"""

                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=analysis_prompt,
                    )

                    st.session_state.analysis_result = response.text
                    st.session_state.current_step = 2
                    st.success("✅ 분석 완료!")

            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
        elif not script_input.strip():
            st.error("❌ 대본을 입력하세요")

with col2:
    if st.button("🔄 초기화", key="reset_btn"):
        st.session_state.script_text = ""
        st.session_state.analysis_result = None
        st.session_state.segments = []
        st.session_state.image_prompts = []
        st.session_state.generated_images = []
        st.session_state.current_step = 1
        st.rerun()

if st.session_state.analysis_result:
    with st.expander("📌 분석 결과", expanded=True):
        st.markdown(st.session_state.analysis_result)

# ============================================================================
# STEP 2: SEGMENT SCRIPT BY DURATION
# ============================================================================
if st.session_state.current_step >= 2:
    st.header("✂️ Step 2: 초 단위 분할")
    st.caption(
        f"설정: {LANGUAGE_CONFIG[selected_language]['label']} | "
        f"{cut_duration}초/컷 | 초당 {chars_per_second}글자 | 컷당 약 {chars_per_cut}글자"
    )

    if st.button("⚡ 대본 분할 시작", key="segment_btn"):
        if not script_input.strip():
            st.error("❌ 먼저 대본을 입력하세요")
        else:
            try:
                with st.spinner("✂️ 대본을 분할 중..."):
                    # 문장 단위로 분할 (자연스러운 경계)
                    sentences = re.split(
                        r'(?<=[.!?。！？])\s*',
                        script_input.strip(),
                    )

                    segments = []
                    current_segment = ""

                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue

                        if len(current_segment) + len(sentence) <= chars_per_cut:
                            current_segment += (" " + sentence) if current_segment else sentence
                        else:
                            if current_segment:
                                segments.append(current_segment)
                            # 문장 자체가 컷 길이보다 긴 경우 강제 분할
                            while len(sentence) > chars_per_cut:
                                segments.append(sentence[:chars_per_cut])
                                sentence = sentence[chars_per_cut:]
                            current_segment = sentence

                    if current_segment:
                        segments.append(current_segment)

                    st.session_state.segments = segments
                    st.session_state.current_step = 3
                    st.success(f"✅ {len(segments)}개 세그먼트로 분할되었습니다")

            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")

    if st.session_state.segments:
        st.subheader("📋 분할된 세그먼트")

        edited_segments = []
        for i, segment in enumerate(st.session_state.segments):
            col_num, col_text = st.columns([0.08, 0.92])
            with col_num:
                st.markdown(f"**{i + 1}.**")
            with col_text:
                edited_text = st.text_input(
                    f"세그먼트 {i + 1}",
                    value=segment,
                    key=f"segment_edit_{i}",
                    label_visibility="collapsed",
                )
                edited_segments.append(edited_text)

        st.session_state.segments = edited_segments

# ============================================================================
# STEP 3: GENERATE IMAGE PROMPTS
# ============================================================================
if st.session_state.current_step >= 3 and st.session_state.segments:
    st.header("🎨 Step 3: 이미지 프롬프트 생성")

    if st.button("✨ 프롬프트 생성 시작", key="prompt_gen_btn"):
        client = get_client()
        if client:
            try:
                generated_prompts = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for idx, segment in enumerate(st.session_state.segments):
                    status_text.text(f"프롬프트 생성 중... ({idx + 1}/{len(st.session_state.segments)})")

                    prompt_gen_instruction = f"""{style_guide}

프롬프트 템플릿:
{prompt_template}

위의 스타일 가이드와 템플릿을 엄격히 따라서, 다음 대본 세그먼트에 맞는 이미지 프롬프트를 생성하세요.

대본: "{segment}"

반드시 아래 형식으로만 응답하세요 (따옴표, 설명 없이 프롬프트 텍스트만):
Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [구체적인 장면 묘사를 영문으로 작성, no text or letters anywhere]"""

                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt_gen_instruction,
                    )

                    generated_prompts.append(response.text.strip().strip('"').strip("'"))
                    progress_bar.progress((idx + 1) / len(st.session_state.segments))

                st.session_state.image_prompts = generated_prompts
                st.session_state.current_step = 4
                status_text.empty()
                st.success("✅ 모든 프롬프트가 생성되었습니다")

            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")

    if st.session_state.image_prompts:
        st.subheader("📝 생성된 이미지 프롬프트 (편집 가능)")

        edited_prompts = []
        for i, prompt in enumerate(st.session_state.image_prompts):
            with st.expander(f"프롬프트 {i + 1}", expanded=False):
                edited_prompt = st.text_area(
                    f"prompt_{i}",
                    value=prompt,
                    height=100,
                    key=f"prompt_edit_{i}",
                    label_visibility="collapsed",
                )
                edited_prompts.append(edited_prompt)

        st.session_state.image_prompts = edited_prompts

# ============================================================================
# STEP 4: GENERATE IMAGES
# ============================================================================
if st.session_state.current_step >= 4 and st.session_state.image_prompts:
    st.header("🖼️ Step 4: 이미지 생성")

    if st.button("🎬 이미지 생성 시작", key="image_gen_btn"):
        client = get_client()
        if client:
            try:
                generated_images = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for idx, prompt in enumerate(st.session_state.image_prompts):
                    status_text.text(f"이미지 생성 중... ({idx + 1}/{len(st.session_state.image_prompts)})")

                    try:
                        response = client.models.generate_content(
                            model="gemini-3.1-flash-image-preview",
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_modalities=["IMAGE"],
                                image_config=types.ImageConfig(
                                    aspect_ratio="16:9",
                                ),
                            ),
                        )

                        if response.candidates and response.candidates[0].content.parts:
                            for part in response.candidates[0].content.parts:
                                if part.inline_data:
                                    image_data = part.inline_data.data
                                    image = Image.open(BytesIO(image_data))
                                    generated_images.append({
                                        "image": image,
                                        "prompt": prompt,
                                        "segment": st.session_state.segments[idx]
                                        if idx < len(st.session_state.segments)
                                        else "",
                                    })
                                    break

                    except Exception as e:
                        st.warning(f"⚠️ 이미지 {idx + 1} 생성 실패: {str(e)}")

                    progress_bar.progress((idx + 1) / len(st.session_state.image_prompts))

                st.session_state.generated_images = generated_images
                status_text.empty()
                st.success(f"✅ {len(generated_images)}개 이미지 생성 완료!")

            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")

    if st.session_state.generated_images:
        st.subheader("🖼️ 생성된 이미지")

        cols = st.columns(3)
        for i, img_data in enumerate(st.session_state.generated_images):
            col = cols[i % 3]
            with col:
                st.image(img_data["image"], use_container_width=True)
                st.caption(f"**세그먼트 {i + 1}**")
                seg_text = img_data["segment"]
                st.text(seg_text[:50] + "..." if len(seg_text) > 50 else seg_text)

        # 다운로드 기능
        st.subheader("📥 다운로드")

        st.write("**개별 이미지:**")
        dl_cols = st.columns(min(len(st.session_state.generated_images), 3))
        for i, img_data in enumerate(st.session_state.generated_images):
            with dl_cols[i % 3]:
                img_bytes = BytesIO()
                img_data["image"].save(img_bytes, format="PNG")
                img_bytes.seek(0)

                st.download_button(
                    label=f"다운로드 {i + 1}",
                    data=img_bytes.getvalue(),
                    file_name=f"image_{i + 1}.png",
                    mime="image/png",
                    key=f"download_{i}",
                )

        st.write("**전체 이미지 (ZIP):**")
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, img_data in enumerate(st.session_state.generated_images):
                img_bytes = BytesIO()
                img_data["image"].save(img_bytes, format="PNG")
                img_bytes.seek(0)
                zip_file.writestr(f"image_{i + 1}.png", img_bytes.getvalue())

        zip_buffer.seek(0)
        st.download_button(
            label="📦 모든 이미지 다운로드 (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="generated_images.zip",
            mime="application/zip",
            key="download_all_zip",
        )

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown(
    "**이미지 생성기 v1.0** | Powered by Gemini API (Nano Banana 2) | "
    f"언어: {LANGUAGE_CONFIG[selected_language]['label']}"
)
