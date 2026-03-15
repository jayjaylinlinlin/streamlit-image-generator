import streamlit as st
import google.genai as genai
from google.genai import types
from io import BytesIO
from PIL import Image
import base64
import re
import zipfile
import json

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Vision Maker v3.2",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# CUSTOM CSS - Screenshot-based UI/UX
# ============================================================================
st.markdown("""
<style>
/* Global */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* Header bar */
.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 0;
    margin-bottom: 1rem;
}
.header-title {
    display: flex;
    align-items: center;
    gap: 12px;
}
.header-title .icon {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 12px;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}
.header-title h1 {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: #1e293b;
}
.header-title .version {
    color: #6366f1;
    font-size: 0.9rem;
    font-weight: 600;
}
.header-subtitle {
    color: #64748b;
    font-size: 0.85rem;
    margin: 0;
}

/* Cards */
.card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* Sidebar character card */
.char-card {
    background: linear-gradient(135deg, #1e1b4b, #312e81);
    border-radius: 16px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    color: white;
}
.char-card .char-name {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

/* Character analysis tags */
.char-tag {
    display: inline-block;
    background: rgba(99, 102, 241, 0.15);
    color: #6366f1;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 0.75rem;
    margin: 2px;
    font-weight: 500;
}

/* Analysis section */
.analysis-item {
    display: flex;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid #f1f5f9;
}
.analysis-label {
    color: #6366f1;
    font-weight: 600;
    font-size: 0.8rem;
    white-space: nowrap;
    min-width: 60px;
}
.analysis-text {
    color: #475569;
    font-size: 0.8rem;
    line-height: 1.5;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #94a3b8;
}
.empty-state .icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}
.empty-state h3 {
    color: #64748b;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
.empty-state p {
    font-size: 0.85rem;
}

/* Intro slider label */
.intro-label {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #475569;
    font-size: 0.85rem;
    font-weight: 500;
}

/* Body info banner */
.body-info {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    color: #166534;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Segment cards */
.segment-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.5rem;
}
.segment-num {
    background: #6366f1;
    color: white;
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Button styles */
.stButton > button {
    border-radius: 12px;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
    transition: all 0.2s;
}

/* Primary action button */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: #fafbfc;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 0.5rem;
}

/* Image grid */
.image-grid-item {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTS & DEFAULTS
# ============================================================================
DEFAULT_PROMPT_TEMPLATE = """Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [action and icon description + no text/letters emphasis]"""

DEFAULT_STYLE_GUIDE = """You are a '2D Stickman Animation Prompt Director'.

Style Guide (Style Lock):
1. Visuals:
 - Characters: Pure-white round faces, single hard cel shading (1-step shadow under chin), thick black outline, thicker torso and neck, stick limbs, flat matte colors.
 - Background: Low saturation flat blocks, absolutely no text.
 - Negative: 3D, photoreal, gradient, soft light, text, letters, speech bubble.

2. Scene Interpretation:
 - Action-focused: Express emotions through eyebrows/mouth lines, actions through clear verbs (leans, points, nods, clasps, gestures).
 - Visualize concepts with person + icons/shapes.
 - Use arrow icons for up/down, chart shapes for data, blank paper icons for documents.
 - All signs, screens, documents use symbols/shapes instead of text.

Output Template:
All prompts must start with the following sentence. Only fill in the [...] part in English:
> Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [action and icon description in English + no text/letters anywhere]"""

LANGUAGE_CONFIG = {
    "Korean": {"chars_per_second": 4.5, "label": "KR Korean"},
    "Japanese": {"chars_per_second": 4.0, "label": "JP Japanese"},
    "English": {"chars_per_second": 3.0, "label": "US English"},
    "Thai": {"chars_per_second": 4.0, "label": "TH Thai"},
    "Chinese": {"chars_per_second": 3.5, "label": "CN Chinese"},
}

# ============================================================================
# SESSION STATE
# ============================================================================
defaults = {
    "api_key": "",
    "intro_text": "",
    "body_text": "",
    "analysis_result": None,
    "char_analysis": None,
    "segments": [],
    "image_prompts": [],
    "generated_images": [],
    "current_step": 1,
    "characters": [],
    "char_image": None,
    "char_image_bytes": None,
    "project_title": "",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ============================================================================
# HELPER: Gemini Client
# ============================================================================
def get_client():
    if not st.session_state.api_key:
        st.error("Please enter your API key in the sidebar.")
        return None
    return genai.Client(api_key=st.session_state.api_key)

def analyze_character_image(client, image_bytes):
    """Analyze uploaded character image and return structured description."""
    img = Image.open(BytesIO(image_bytes))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    prompt = """Analyze this character image in detail. Return a JSON object with these exact keys (all values in Korean):
{
  "name_guess": "character name or type guess",
  "face": "face shape, expression, features",
  "hair": "hair style, color, length",
  "body": "body type, proportions",
  "outfit": "clothing description",
  "accessories": "accessories, items held",
  "style": "art style description",
  "colors": "main color palette",
  "tags": ["tag1", "tag2", "tag3"]
}
Return ONLY valid JSON, no markdown or explanation."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
            prompt,
        ],
    )

    text = response.text.strip()
    # Extract JSON from response
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        return json.loads(json_match.group())
    return None

# ============================================================================
# SIDEBAR - Character Panel
# ============================================================================
with st.sidebar:
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="Enter API key...",
    )
    st.session_state.api_key = api_key_input

    st.divider()

    # Character image upload
    char_name_input = st.text_input(
        "Character Name",
        value=st.session_state.characters[0]["name"] if st.session_state.characters else "",
        placeholder="e.g. Character name",
        key="sidebar_char_name",
    )

    uploaded_file = st.file_uploader(
        "Upload Character Image",
        type=["png", "jpg", "jpeg", "webp"],
        key="char_upload",
    )

    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        st.session_state.char_image_bytes = image_bytes
        st.image(image_bytes, use_container_width=True)

        # Buttons row
        col_a, col_e, col_d = st.columns(3)
        with col_a:
            analyze_char = st.button("Analyze", key="analyze_char_btn", use_container_width=True)
        with col_e:
            edit_char = st.button("Edit", key="edit_char_btn", use_container_width=True)
        with col_d:
            delete_char = st.button("Delete", key="delete_char_btn", use_container_width=True)

        if analyze_char:
            client = get_client()
            if client:
                with st.spinner("Analyzing character..."):
                    try:
                        analysis = analyze_character_image(client, image_bytes)
                        if analysis:
                            st.session_state.char_analysis = analysis
                            # Update character list
                            char_data = {
                                "name": char_name_input or analysis.get("name_guess", "Character"),
                                "appearance": json.dumps(analysis, ensure_ascii=False),
                                "color": "#6366f1",
                                "image_bytes": image_bytes,
                            }
                            if st.session_state.characters:
                                st.session_state.characters[0] = char_data
                            else:
                                st.session_state.characters.append(char_data)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")

        if delete_char:
            st.session_state.char_image_bytes = None
            st.session_state.char_analysis = None
            st.session_state.characters = []
            st.rerun()
    elif st.session_state.char_image_bytes:
        st.image(st.session_state.char_image_bytes, use_container_width=True)

    # Update character name
    if char_name_input and st.session_state.characters:
        st.session_state.characters[0]["name"] = char_name_input

    # Display character analysis
    if st.session_state.char_analysis:
        analysis = st.session_state.char_analysis
        with st.expander("Analysis - JSON", expanded=True):
            analysis_fields = {
                "Face": "face",
                "Hair": "hair",
                "Body": "body",
                "Outfit": "outfit",
                "Accessories": "accessories",
                "Style": "style",
                "Colors": "colors",
            }
            for label, key in analysis_fields.items():
                if key in analysis and analysis[key]:
                    st.markdown(f"**{label}**")
                    st.caption(analysis[key])

            # Tags
            if "tags" in analysis and analysis["tags"]:
                st.markdown("**Tags**")
                tags_html = " ".join(
                    f'<span class="char-tag">{t}</span>' for t in analysis["tags"]
                )
                st.markdown(tags_html, unsafe_allow_html=True)

    st.divider()

    # Language & Duration
    selected_language = st.selectbox(
        "Script Language",
        options=list(LANGUAGE_CONFIG.keys()),
        format_func=lambda x: LANGUAGE_CONFIG[x]["label"],
    )

    cut_duration = st.select_slider(
        "Cut Duration (sec)",
        options=[5, 10, 15, 20, 25, 30],
        value=5,
    )

    chars_per_second = LANGUAGE_CONFIG[selected_language]["chars_per_second"]
    chars_per_cut = int(cut_duration * chars_per_second)

    st.divider()

    # Style guide (collapsed)
    with st.expander("Prompt Template"):
        prompt_template = st.text_area(
            "Template",
            value=DEFAULT_PROMPT_TEMPLATE,
            height=100,
            label_visibility="collapsed",
        )

    with st.expander("Style Guide"):
        style_guide = st.text_area(
            "Guide",
            value=DEFAULT_STYLE_GUIDE,
            height=200,
            label_visibility="collapsed",
        )

# ============================================================================
# MAIN AREA - Header
# ============================================================================
header_cols = st.columns([6, 2, 2])
with header_cols[0]:
    st.markdown("""
    <div class="header-title">
        <div class="icon">🎬</div>
        <div>
            <h1 style="display:inline;">Vision Maker</h1>
            <span class="version">v3.2</span>
            <p class="header-subtitle">Transform scripts into high-quality AI visual productions instantly.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with header_cols[1]:
    split_btn = st.button("Split Scenes", key="split_btn", use_container_width=True)
with header_cols[2]:
    batch_btn = st.button("Batch Generate", key="batch_btn", type="primary", use_container_width=True)

st.divider()

# ============================================================================
# SCRIPT INPUT - Intro / Body split
# ============================================================================
intro_col, body_col = st.columns(2)

with intro_col:
    intro_text = st.text_area(
        "Intro Script",
        value=st.session_state.intro_text,
        height=180,
        placeholder="Paste your concise intro script here...",
        key="intro_input",
    )
    st.session_state.intro_text = intro_text

    # Intro duration slider
    intro_duration = st.slider(
        "Intro Duration",
        min_value=3,
        max_value=15,
        value=6,
        step=1,
        format="%ds",
        key="intro_dur_slider",
    )

with body_col:
    body_text = st.text_area(
        "Body Script",
        value=st.session_state.body_text,
        height=180,
        placeholder="Enter body content here...",
        key="body_input",
    )
    st.session_state.body_text = body_text

    st.markdown(
        f'<div class="body-info">Body is split based on the configured time ({cut_duration}s).</div>',
        unsafe_allow_html=True,
    )

# Project title
project_title = st.text_input(
    "Project Title",
    value=st.session_state.project_title,
    placeholder="e.g. Samsung Next-Gen EV Battery Strategy Analysis",
    key="proj_title",
)
st.session_state.project_title = project_title

st.divider()

# ============================================================================
# SPLIT SCENES - Process
# ============================================================================
def split_script_into_segments(intro, body, intro_dur, body_cut_dur, cps):
    """Split intro and body into segments."""
    segments = []

    # Intro segment(s)
    if intro.strip():
        intro_chars = int(intro_dur * cps)
        if len(intro.strip()) <= intro_chars:
            segments.append({"type": "intro", "text": intro.strip()})
        else:
            text = intro.strip()
            while text:
                segments.append({"type": "intro", "text": text[:intro_chars]})
                text = text[intro_chars:]

    # Body segments
    if body.strip():
        body_chars = int(body_cut_dur * cps)
        sentences = re.split(r'(?<=[.!?\u3002\uff01\uff1f])\s*', body.strip())
        current = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(current) + len(sentence) <= body_chars:
                current += (" " + sentence) if current else sentence
            else:
                if current:
                    segments.append({"type": "body", "text": current})
                while len(sentence) > body_chars:
                    segments.append({"type": "body", "text": sentence[:body_chars]})
                    sentence = sentence[body_chars:]
                current = sentence
        if current:
            segments.append({"type": "body", "text": current})

    return segments

if split_btn:
    combined = (intro_text.strip() or "") + (body_text.strip() or "")
    if not combined:
        st.error("Please enter a script (intro or body).")
    else:
        segments = split_script_into_segments(
            intro_text, body_text, intro_duration, cut_duration, chars_per_second
        )
        st.session_state.segments = segments
        st.session_state.current_step = 3
        st.rerun()

# ============================================================================
# BATCH GENERATE - Full pipeline
# ============================================================================
if batch_btn:
    combined = (intro_text.strip() or "") + (body_text.strip() or "")
    if not combined:
        st.error("Please enter a script first.")
    else:
        client = get_client()
        if client:
            # Step 1: Split
            if not st.session_state.segments:
                segments = split_script_into_segments(
                    intro_text, body_text, intro_duration, cut_duration, chars_per_second
                )
                st.session_state.segments = segments

            # Step 2: Generate prompts
            try:
                generated_prompts = []
                progress_bar = st.progress(0, text="Generating prompts...")

                # Build character description for prompts
                char_desc = ""
                if st.session_state.characters:
                    c = st.session_state.characters[0]
                    char_desc = f"\nCharacter to include: {c['name']}"
                    if st.session_state.char_analysis:
                        a = st.session_state.char_analysis
                        details = []
                        for k in ["face", "hair", "body", "outfit", "accessories", "style", "colors"]:
                            if k in a and a[k]:
                                details.append(f"{k}: {a[k]}")
                        if details:
                            char_desc += " (" + ", ".join(details) + ")"

                total = len(st.session_state.segments)
                for idx, seg in enumerate(st.session_state.segments):
                    progress_bar.progress(
                        (idx) / (total * 2),
                        text=f"Generating prompt {idx + 1}/{total}...",
                    )

                    instruction = f"""{style_guide}

Prompt template:
{prompt_template}
{char_desc}

Generate an image prompt for this script segment following the style guide strictly.
If a character is defined, include their visual features in the prompt.

Segment type: {seg['type']}
Script: "{seg['text']}"

Respond with ONLY the prompt text (no quotes, no explanation):
Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [specific scene description in English, no text or letters anywhere]"""

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=instruction,
                    )
                    generated_prompts.append(response.text.strip().strip('"').strip("'"))

                st.session_state.image_prompts = generated_prompts

                # Step 3: Generate images
                generated_images = []
                for idx, prompt in enumerate(generated_prompts):
                    progress_bar.progress(
                        (total + idx) / (total * 2),
                        text=f"Generating image {idx + 1}/{total}...",
                    )

                    try:
                        # Build contents with character reference image if available
                        contents = [prompt]
                        if st.session_state.char_image_bytes:
                            ref_img = Image.open(BytesIO(st.session_state.char_image_bytes))
                            buf = BytesIO()
                            ref_img.save(buf, format="PNG")
                            buf.seek(0)
                            contents = [
                                types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
                                f"Using the character from the reference image above, generate: {prompt}",
                            ]

                        response = client.models.generate_content(
                            model="gemini-2.5-flash-preview-image-generation",
                            contents=contents,
                            config=types.GenerateContentConfig(
                                response_modalities=["IMAGE", "TEXT"],
                            ),
                        )

                        if response.candidates and response.candidates[0].content.parts:
                            for part in response.candidates[0].content.parts:
                                if part.inline_data:
                                    image_data = part.inline_data.data
                                    image = Image.open(BytesIO(image_data))
                                    seg_data = st.session_state.segments[idx] if idx < len(st.session_state.segments) else {"type": "", "text": ""}
                                    generated_images.append({
                                        "image": image,
                                        "prompt": prompt,
                                        "segment": seg_data["text"],
                                        "type": seg_data["type"],
                                    })
                                    break

                    except Exception as e:
                        st.warning(f"Image {idx + 1} failed: {str(e)}")

                st.session_state.generated_images = generated_images
                st.session_state.current_step = 4
                progress_bar.empty()
                st.success(f"{len(generated_images)} images generated!")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# SEGMENTS DISPLAY
# ============================================================================
if st.session_state.segments:
    st.subheader("Segments")

    edited_segments = []
    for i, seg in enumerate(st.session_state.segments):
        type_label = "INTRO" if seg["type"] == "intro" else "BODY"
        type_color = "#8b5cf6" if seg["type"] == "intro" else "#3b82f6"

        col_tag, col_text = st.columns([0.08, 0.92])
        with col_tag:
            st.markdown(
                f'<span style="background:{type_color};color:white;border-radius:8px;'
                f'padding:2px 8px;font-size:0.7rem;font-weight:600;">{type_label} {i+1}</span>',
                unsafe_allow_html=True,
            )
        with col_text:
            edited = st.text_input(
                f"seg_{i}",
                value=seg["text"],
                key=f"seg_edit_{i}",
                label_visibility="collapsed",
            )
            edited_segments.append({"type": seg["type"], "text": edited})

    st.session_state.segments = edited_segments

# ============================================================================
# GENERATED IMAGES DISPLAY
# ============================================================================
if st.session_state.generated_images:
    st.divider()
    st.subheader("Generated Images")

    cols = st.columns(3)
    for i, img_data in enumerate(st.session_state.generated_images):
        with cols[i % 3]:
            st.image(img_data["image"], use_container_width=True)
            type_label = img_data.get("type", "body").upper()
            st.caption(f"**{type_label} {i + 1}**")
            seg_text = img_data["segment"]
            st.text(seg_text[:60] + "..." if len(seg_text) > 60 else seg_text)

    # Download section
    st.divider()
    st.subheader("Download")

    dl_cols = st.columns(min(len(st.session_state.generated_images), 3))
    for i, img_data in enumerate(st.session_state.generated_images):
        with dl_cols[i % 3]:
            img_bytes = BytesIO()
            img_data["image"].save(img_bytes, format="PNG")
            img_bytes.seek(0)
            st.download_button(
                label=f"Download {i + 1}",
                data=img_bytes.getvalue(),
                file_name=f"image_{i + 1}.png",
                mime="image/png",
                key=f"dl_{i}",
            )

    # ZIP download
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, img_data in enumerate(st.session_state.generated_images):
            img_bytes = BytesIO()
            img_data["image"].save(img_bytes, format="PNG")
            img_bytes.seek(0)
            zf.writestr(f"image_{i + 1}.png", img_bytes.getvalue())
    zip_buffer.seek(0)

    st.download_button(
        label="Download All (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="generated_images.zip",
        mime="application/zip",
        key="dl_all_zip",
    )

# ============================================================================
# EMPTY STATE
# ============================================================================
if not st.session_state.generated_images and not st.session_state.segments:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🖼️</div>
        <h3>Your vision starts here</h3>
        <p>Enter a script and click 'Batch Generate' to begin.</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.caption(
    f"Vision Maker v3.2 | Powered by Gemini API | "
    f"Language: {LANGUAGE_CONFIG[selected_language]['label']}"
)
