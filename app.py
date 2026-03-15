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
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #252640 !important;
    border: 1px solid #3d3e5c !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div > div {
    color: #e2e8f0 !important;
}

/* Sidebar section labels */
.sidebar-label {
    color: #a78bfa !important;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Character card in sidebar */
.char-slot {
    background: #252640;
    border: 2px solid #6366f1;
    border-radius: 14px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.char-slot .char-name {
    font-weight: 600;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.char-slot .char-name img {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    object-fit: cover;
}
.char-slot .char-actions {
    display: flex;
    gap: 6px;
}
.char-slot .char-actions span {
    cursor: pointer;
    opacity: 0.7;
}

/* Model selection cards */
.model-card {
    background: #252640;
    border: 2px solid transparent;
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 6px;
    cursor: pointer;
}
.model-card.active {
    border-color: #6366f1;
    background: #2d2e50;
}
.model-card .model-name {
    font-weight: 600;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 6px;
}
.model-card .model-desc {
    font-size: 0.75rem;
    color: #94a3b8 !important;
    margin-top: 2px;
}

/* Analysis section */
.analysis-section {
    background: #1e1f38;
    border-radius: 12px;
    padding: 12px;
    margin-top: 8px;
}
.analysis-row {
    display: flex;
    gap: 8px;
    padding: 6px 0;
    border-bottom: 1px solid #2d2e50;
    font-size: 0.78rem;
    line-height: 1.5;
}
.analysis-row:last-child { border-bottom: none; }
.analysis-key {
    color: #a78bfa !important;
    font-weight: 600;
    min-width: 50px;
    white-space: nowrap;
}
.analysis-val {
    color: #cbd5e1 !important;
}

/* Tag chips */
.tag-chip {
    display: inline-block;
    background: rgba(99,102,241,0.2);
    color: #a78bfa !important;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 0.7rem;
    margin: 2px;
    font-weight: 500;
}

/* Main area */
.block-container { padding-top: 1rem; }

/* Header */
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

/* Intro slider row */
.intro-row {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 12px;
    padding: 6px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #166534;
    font-size: 0.85rem;
    font-weight: 500;
}
.body-info {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 12px;
    padding: 8px 14px;
    color: #166534;
    font-size: 0.82rem;
}

/* Slot save button */
.slot-btn {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 8px 0;
    width: 100%;
    text-align: center;
    font-weight: 600;
    font-size: 0.85rem;
    cursor: pointer;
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

/* Segment tag */
.seg-tag {
    display: inline-block;
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTS
# ============================================================================
DEFAULT_PROMPT_TEMPLATE = """Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [action and icon description + no text/letters emphasis]"""

DEFAULT_STYLE_GUIDE = """You are a '2D Stickman Animation Prompt Director'.

Style Guide:
1. Visuals:
 - Characters: Pure-white round faces, single hard cel shading, thick black outline, thicker torso and neck, stick limbs, flat matte colors.
 - Background: Low saturation flat blocks, absolutely no text.
 - Negative: 3D, photoreal, gradient, soft light, text, letters, speech bubble.

2. Scene Interpretation:
 - Action-focused: emotions via eyebrows/mouth, actions via clear verbs.
 - Visualize concepts with person + icons/shapes.
 - All signs/screens/documents use symbols instead of text.

Output: Start every prompt with:
> Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [English description, no text/letters anywhere]"""

LANGUAGE_CONFIG = {
    "Korean": {"chars_per_second": 4.5, "label": "Korean"},
    "Japanese": {"chars_per_second": 4.0, "label": "Japanese"},
    "English": {"chars_per_second": 3.0, "label": "English"},
    "Thai": {"chars_per_second": 4.0, "label": "Thai"},
    "Chinese": {"chars_per_second": 3.5, "label": "Chinese"},
}

MODEL_CONFIG = {
    "nano_banana_pro": {
        "id": "gemini-2.5-flash-preview-image-generation",
        "name": "Nano Banana Pro",
        "desc": "Highest quality",
        "icon": "🔥",
    },
    "nano_banana_2": {
        "id": "gemini-2.5-flash-preview-image-generation",
        "name": "Nano Banana 2",
        "desc": "Fast",
        "icon": "🔥",
    },
}

# ============================================================================
# SESSION STATE
# ============================================================================
defaults = {
    "api_key": "",
    "intro_text": "",
    "body_text": "",
    "segments": [],
    "image_prompts": [],
    "generated_images": [],
    "current_step": 1,
    "char_slots": [None, None],  # 2 character slots
    "active_slot": 0,
    "char_analysis": None,
    "char_image_bytes": None,
    "char_extra_features": "",
    "selected_model": "nano_banana_pro",
    "project_title": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def get_client():
    if not st.session_state.api_key:
        st.error("Please enter API key in sidebar.")
        return None
    return genai.Client(api_key=st.session_state.api_key)


def analyze_character_image(client, image_bytes):
    img = Image.open(BytesIO(image_bytes))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    prompt = """Analyze this character image in detail. Return a JSON object with these keys (values in Korean):
{
  "name_guess": "character name/type guess",
  "face": "face details",
  "hair": "hair details",
  "body_shape": "body type",
  "outfit": "clothing",
  "accessories": "accessories",
  "style": "art style",
  "unique": "unique features",
  "tags": ["tag1", "tag2", "tag3"]
}
Return ONLY valid JSON."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
            prompt,
        ],
    )

    text = response.text.strip()
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        return json.loads(m.group())
    return None


def build_char_description():
    """Build character description string for prompt generation."""
    slot = st.session_state.char_slots[st.session_state.active_slot]
    if not slot:
        return ""

    parts = [f"\nCharacter: {slot['name']}"]
    if slot.get("analysis"):
        a = slot["analysis"]
        for k in ["face", "hair", "body_shape", "outfit", "accessories", "style", "unique"]:
            if k in a and a[k]:
                parts.append(f"  {k}: {a[k]}")
    if st.session_state.char_extra_features.strip():
        parts.append(f"  extra: {st.session_state.char_extra_features.strip()}")
    return "\n".join(parts)


# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    # API Key (small, at top)
    api_key_input = st.text_input(
        "API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="Gemini API Key",
        label_visibility="collapsed",
    )
    st.session_state.api_key = api_key_input

    st.markdown('<div class="sidebar-label">✨ Character Consistency</div>', unsafe_allow_html=True)

    # Show saved slot count
    filled = sum(1 for s in st.session_state.char_slots if s is not None)
    st.caption(f"Saved characters ({filled}/2)")

    # Display saved character slots
    for i, slot in enumerate(st.session_state.char_slots):
        if slot is not None:
            is_active = i == st.session_state.active_slot
            border_color = "#6366f1" if is_active else "#3d3e5c"

            # Character slot card
            cols = st.columns([0.15, 0.6, 0.12, 0.13])
            with cols[0]:
                if slot.get("thumb"):
                    st.image(slot["thumb"], width=30)
                else:
                    st.markdown("👤")
            with cols[1]:
                if st.button(slot["name"], key=f"select_slot_{i}", use_container_width=True):
                    st.session_state.active_slot = i
                    if slot.get("analysis"):
                        st.session_state.char_analysis = slot["analysis"]
                    if slot.get("image_bytes"):
                        st.session_state.char_image_bytes = slot["image_bytes"]
                    st.rerun()
            with cols[2]:
                if st.button("📋", key=f"copy_slot_{i}"):
                    pass  # Copy placeholder
            with cols[3]:
                if st.button("🗑️", key=f"del_slot_{i}"):
                    st.session_state.char_slots[i] = None
                    if st.session_state.active_slot == i:
                        st.session_state.char_analysis = None
                        st.session_state.char_image_bytes = None
                    st.rerun()

    # Character upload
    char_name = st.text_input(
        "Character Name",
        value="",
        placeholder="Character name",
        key="char_name_input",
    )

    uploaded = st.file_uploader(
        "Upload Character",
        type=["png", "jpg", "jpeg", "webp"],
        key="char_uploader",
        label_visibility="collapsed",
    )

    if uploaded:
        img_bytes = uploaded.getvalue()
        st.session_state.char_image_bytes = img_bytes
        st.image(img_bytes, use_container_width=True)

        # Save to slot button
        if st.button(
            f"Save to Slot ({st.session_state.active_slot + 1}/2)",
            key="save_slot_btn",
            use_container_width=True,
            type="primary",
        ):
            client = get_client()
            if client:
                with st.spinner("Analyzing character..."):
                    try:
                        analysis = analyze_character_image(client, img_bytes)
                        # Create thumbnail
                        thumb = Image.open(BytesIO(img_bytes))
                        thumb.thumbnail((60, 60))
                        thumb_buf = BytesIO()
                        thumb.save(thumb_buf, format="PNG")

                        slot_data = {
                            "name": char_name or (analysis.get("name_guess", "Character") if analysis else "Character"),
                            "image_bytes": img_bytes,
                            "thumb": thumb_buf.getvalue(),
                            "analysis": analysis,
                        }

                        st.session_state.char_slots[st.session_state.active_slot] = slot_data
                        st.session_state.char_analysis = analysis
                        st.success("Saved!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    elif st.session_state.char_image_bytes:
        st.image(st.session_state.char_image_bytes, use_container_width=True)

    # Analysis display
    if st.session_state.char_analysis:
        analysis = st.session_state.char_analysis
        with st.expander("Analysis - JSON", expanded=True):
            labels = {
                "face": "😊 Face",
                "hair": "💇 Hair",
                "body_shape": "🏋 Body",
                "outfit": "👔 Outfit",
                "accessories": "💎 Accessories",
                "style": "🎨 Style",
                "unique": "⭐ Unique",
            }
            for key, label in labels.items():
                if key in analysis and analysis[key]:
                    st.markdown(f"**{label}**")
                    st.caption(analysis[key])

            if "tags" in analysis and analysis["tags"]:
                tags_html = " ".join(f'<span class="tag-chip">{t}</span>' for t in analysis["tags"])
                st.markdown(tags_html, unsafe_allow_html=True)

    # Extra features
    st.markdown('<div class="sidebar-label">📝 Extra Features (Optional)</div>', unsafe_allow_html=True)
    extra = st.text_area(
        "extra_features",
        value=st.session_state.char_extra_features,
        height=80,
        placeholder="e.g. always smiling, hands in pockets...",
        label_visibility="collapsed",
    )
    st.session_state.char_extra_features = extra

    st.divider()

    # Model selection
    st.markdown('<div class="sidebar-label">📦 Generation Model</div>', unsafe_allow_html=True)

    for model_key, model_info in MODEL_CONFIG.items():
        is_selected = st.session_state.selected_model == model_key
        label = f"{model_info['icon']} {model_info['name']}"
        if is_selected:
            label += " ✅"
        if st.button(
            label,
            key=f"model_{model_key}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
            help=model_info["desc"],
        ):
            st.session_state.selected_model = model_key
            st.rerun()
        st.caption(model_info["desc"])

    st.divider()

    # Output language
    st.markdown('<div class="sidebar-label">🌐 Output Language</div>', unsafe_allow_html=True)
    selected_language = st.selectbox(
        "lang",
        options=list(LANGUAGE_CONFIG.keys()),
        format_func=lambda x: LANGUAGE_CONFIG[x]["label"],
        label_visibility="collapsed",
    )

    st.divider()

    # Scene time
    st.markdown('<div class="sidebar-label">⏱️ Scene Time</div>', unsafe_allow_html=True)
    cut_duration = st.slider(
        "cut_dur",
        min_value=5,
        max_value=30,
        value=20,
        step=5,
        format="%ds",
        label_visibility="collapsed",
    )
    chars_per_second = LANGUAGE_CONFIG[selected_language]["chars_per_second"]
    chars_per_cut = int(cut_duration * chars_per_second)
    st.caption(f"~{chars_per_cut} chars per segment")

    st.divider()

    # Style guide (collapsed)
    with st.expander("Prompt Template"):
        prompt_template = st.text_area(
            "tmpl", value=DEFAULT_PROMPT_TEMPLATE, height=80, label_visibility="collapsed"
        )
    with st.expander("Style Guide"):
        style_guide = st.text_area(
            "guide", value=DEFAULT_STYLE_GUIDE, height=150, label_visibility="collapsed"
        )

# ============================================================================
# MAIN - Header
# ============================================================================
h_cols = st.columns([6, 2, 2])
with h_cols[0]:
    st.markdown("""
    <div class="main-header">
        <div class="icon-box">🎬</div>
        <div>
            <h1 style="display:inline">Vision Maker</h1>
            <span class="ver">v3.2</span>
            <p class="sub">Transform scripts to high-quality AI visual productions instantly.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with h_cols[1]:
    split_btn = st.button("✂️ Split Scenes", key="split_btn", use_container_width=True)
with h_cols[2]:
    batch_btn = st.button("⚡ Batch Generate", key="batch_btn", type="primary", use_container_width=True)

st.divider()

# ============================================================================
# SCRIPT INPUT - Intro / Body
# ============================================================================
intro_col, body_col = st.columns(2)

with intro_col:
    intro_text = st.text_area(
        "Intro Script",
        value=st.session_state.intro_text,
        height=160,
        placeholder="Paste your concise intro script here...",
        label_visibility="collapsed",
    )
    st.session_state.intro_text = intro_text

with body_col:
    body_text = st.text_area(
        "Body Script",
        value=st.session_state.body_text,
        height=160,
        placeholder="Enter body content here...",
        label_visibility="collapsed",
    )
    st.session_state.body_text = body_text

# Intro slider & body info
i_col, b_col = st.columns(2)
with i_col:
    intro_duration = st.slider(
        "Intro Duration",
        min_value=3, max_value=15, value=6, step=1, format="%ds",
    )
with b_col:
    st.markdown(
        f'<div class="body-info">ℹ️ Body is split based on configured scene time ({cut_duration}s).</div>',
        unsafe_allow_html=True,
    )

# Project title
st.text_input(
    "Project Title",
    value=st.session_state.project_title,
    placeholder="e.g. Samsung Next-Gen EV Battery Strategy Analysis",
    key="proj_title_input",
)
st.session_state.project_title = st.session_state.get("proj_title_input", "")

st.divider()

# ============================================================================
# SPLIT LOGIC
# ============================================================================
def split_segments(intro, body, intro_dur, body_cut_dur, cps):
    segs = []
    if intro.strip():
        ic = int(intro_dur * cps)
        text = intro.strip()
        while text:
            segs.append({"type": "intro", "text": text[:ic]})
            text = text[ic:]
    if body.strip():
        bc = int(body_cut_dur * cps)
        sentences = re.split(r'(?<=[.!?\u3002\uff01\uff1f])\s*', body.strip())
        cur = ""
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if len(cur) + len(s) <= bc:
                cur += (" " + s) if cur else s
            else:
                if cur:
                    segs.append({"type": "body", "text": cur})
                while len(s) > bc:
                    segs.append({"type": "body", "text": s[:bc]})
                    s = s[bc:]
                cur = s
        if cur:
            segs.append({"type": "body", "text": cur})
    return segs

# ============================================================================
# SPLIT BUTTON
# ============================================================================
if split_btn:
    combined = (intro_text.strip() or "") + (body_text.strip() or "")
    if not combined:
        st.error("Please enter a script.")
    else:
        segs = split_segments(intro_text, body_text, intro_duration, cut_duration, chars_per_second)
        st.session_state.segments = segs
        st.session_state.current_step = 3
        st.rerun()

# ============================================================================
# BATCH GENERATE
# ============================================================================
if batch_btn:
    combined = (intro_text.strip() or "") + (body_text.strip() or "")
    if not combined:
        st.error("Please enter a script.")
    else:
        client = get_client()
        if client:
            # Split if not done
            if not st.session_state.segments:
                segs = split_segments(intro_text, body_text, intro_duration, cut_duration, chars_per_second)
                st.session_state.segments = segs

            model_id = MODEL_CONFIG[st.session_state.selected_model]["id"]
            char_desc = build_char_description()
            total = len(st.session_state.segments)

            try:
                # Step 1: Generate prompts
                prompts = []
                progress = st.progress(0, text="Generating prompts...")

                for idx, seg in enumerate(st.session_state.segments):
                    progress.progress(idx / (total * 2), text=f"Prompt {idx+1}/{total}...")

                    instruction = f"""{style_guide}

Prompt template: {prompt_template}
{char_desc}

Generate an image prompt for this segment. Include character visual features if defined.

Segment ({seg['type']}): "{seg['text']}"

Respond ONLY with the prompt text:
Upgraded stick-man 2D with thick black outline, pure white faces, single hard cel shading, thicker torso and neck, flat matte colors; SCENE: [English description, no text/letters anywhere]"""

                    resp = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=instruction,
                    )
                    prompts.append(resp.text.strip().strip('"').strip("'"))

                st.session_state.image_prompts = prompts

                # Step 2: Generate images using character reference
                images = []
                slot = st.session_state.char_slots[st.session_state.active_slot]

                for idx, prompt in enumerate(prompts):
                    progress.progress((total + idx) / (total * 2), text=f"Image {idx+1}/{total}...")

                    try:
                        # Build contents - include character reference image if available
                        if slot and slot.get("image_bytes"):
                            ref_buf = BytesIO()
                            ref_img = Image.open(BytesIO(slot["image_bytes"]))
                            ref_img.save(ref_buf, format="PNG")
                            ref_buf.seek(0)
                            contents = [
                                types.Part.from_bytes(data=ref_buf.getvalue(), mime_type="image/png"),
                                f"Using the character from this reference image, generate the following scene. Keep the character's appearance consistent: {prompt}",
                            ]
                        else:
                            contents = [prompt]

                        resp = client.models.generate_content(
                            model=model_id,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                response_modalities=["IMAGE", "TEXT"],
                            ),
                        )

                        if resp.candidates and resp.candidates[0].content.parts:
                            for part in resp.candidates[0].content.parts:
                                if part.inline_data:
                                    img = Image.open(BytesIO(part.inline_data.data))
                                    seg_data = st.session_state.segments[idx] if idx < len(st.session_state.segments) else {"type": "", "text": ""}
                                    images.append({
                                        "image": img,
                                        "prompt": prompt,
                                        "segment": seg_data["text"],
                                        "type": seg_data["type"],
                                    })
                                    break

                    except Exception as e:
                        st.warning(f"Image {idx+1} failed: {str(e)}")

                st.session_state.generated_images = images
                st.session_state.current_step = 4
                progress.empty()
                st.success(f"{len(images)} images generated!")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# SEGMENTS DISPLAY
# ============================================================================
if st.session_state.segments:
    st.subheader("Segments")
    edited = []
    for i, seg in enumerate(st.session_state.segments):
        t_label = "INTRO" if seg["type"] == "intro" else "BODY"
        t_color = "#8b5cf6" if seg["type"] == "intro" else "#3b82f6"
        c1, c2 = st.columns([0.08, 0.92])
        with c1:
            st.markdown(f'<span class="seg-tag" style="background:{t_color}">{t_label} {i+1}</span>', unsafe_allow_html=True)
        with c2:
            val = st.text_input(f"s{i}", value=seg["text"], key=f"se_{i}", label_visibility="collapsed")
            edited.append({"type": seg["type"], "text": val})
    st.session_state.segments = edited

# ============================================================================
# GENERATED IMAGES
# ============================================================================
if st.session_state.generated_images:
    st.divider()
    st.subheader("Generated Images")

    cols = st.columns(3)
    for i, d in enumerate(st.session_state.generated_images):
        with cols[i % 3]:
            st.image(d["image"], use_container_width=True)
            st.caption(f"**{d.get('type','').upper()} {i+1}**")
            t = d["segment"]
            st.text(t[:60] + "..." if len(t) > 60 else t)

    st.divider()
    st.subheader("Download")

    dl_cols = st.columns(min(len(st.session_state.generated_images), 3))
    for i, d in enumerate(st.session_state.generated_images):
        with dl_cols[i % 3]:
            buf = BytesIO()
            d["image"].save(buf, format="PNG")
            buf.seek(0)
            st.download_button(f"Download {i+1}", buf.getvalue(), f"image_{i+1}.png", "image/png", key=f"dl_{i}")

    zbuf = BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, d in enumerate(st.session_state.generated_images):
            buf = BytesIO()
            d["image"].save(buf, format="PNG")
            buf.seek(0)
            zf.writestr(f"image_{i+1}.png", buf.getvalue())
    zbuf.seek(0)
    st.download_button("Download All (ZIP)", zbuf.getvalue(), "generated_images.zip", "application/zip", key="dl_zip")

# ============================================================================
# EMPTY STATE
# ============================================================================
if not st.session_state.generated_images and not st.session_state.segments:
    st.markdown("""
    <div class="empty-state">
        <div class="big-icon">🖼️</div>
        <h3>Your vision starts here</h3>
        <p>Enter a script and click 'Batch Generate' to begin.</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.caption(f"Vision Maker v3.2 | Powered by Gemini API | {LANGUAGE_CONFIG[selected_language]['label']}")
