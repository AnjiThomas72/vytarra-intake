from __future__ import annotations
import os
import json
import base64
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from streamlit_drawable_canvas import st_canvas

# -----------------------------
# Config
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo.png"
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    try:
        DATABASE_URL = st.secrets["DATABASE_URL"]
    except Exception:
        pass

st.set_page_config(
    page_title="VYTARRA™ Intake",
    page_icon="🟢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp {
        background: linear-gradient(160deg, #d4e0cc 0%, #eef4e6 20%, #c8d8bc 40%, #e8f0de 60%, #d0dcc6 80%, #eaf2e4 100%);
        min-height: 100vh;
        font-family: 'Inter', sans-serif;
    }
    .intake-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px 40px;
        margin: 20px auto;
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    .section-header {
        color: #1f4e79;
        font-size: 18px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 16px;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 2px solid #5a8a5a;
    }
    .compliance-text {
        background: #f8fafb;
        border-left: 4px solid #1f4e79;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 12px 0;
        font-size: 13px;
        line-height: 1.7;
        color: #1a1a2e;
    }
    .sig-label {
        font-weight: 700;
        color: #1f4e79;
        font-size: 14px;
        margin-bottom: 4px;
    }
    .intake-title {
        color: #1f4e79;
        font-size: 26px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-align: center;
        margin-top: 16px;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 2px solid #5a8a5a;
    }
    /* Shrink the metric (cm / kg) values */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Database
# -----------------------------
def _pg_conn():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def _ensure_intake_table():
    if not DATABASE_URL:
        return
    try:
        with _pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS client_intake (
                        id SERIAL PRIMARY KEY,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        full_name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        phone TEXT,
                        date_of_birth TEXT,
                        weight_kg TEXT,
                        height_cm TEXT,
                        has_pacemaker BOOLEAN DEFAULT FALSE,
                        has_conditions BOOLEAN DEFAULT FALSE,
                        takes_medications BOOLEAN DEFAULT FALSE,
                        recent_procedures BOOLEAN DEFAULT FALSE,
                        smokes_or_drinks BOOLEAN DEFAULT FALSE,
                        health_concerns TEXT,
                        intake_signature TEXT,
                        compliance_signature TEXT,
                        claimed_by TEXT,
                        claimed_at TEXT,
                        created_at TEXT NOT NULL,
                        lang TEXT DEFAULT 'en'
                    )
                """)
            conn.commit()
    except Exception:
        pass


def save_intake(data: dict) -> bool:
    if not DATABASE_URL:
        st.error("Database not configured.")
        return False
    _ensure_intake_table()
    try:
        now = datetime.now(timezone.utc).isoformat()
        with _pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO client_intake (
                        first_name, last_name, full_name, email, phone,
                        date_of_birth, weight_kg, height_cm,
                        has_pacemaker, has_conditions, takes_medications,
                        recent_procedures, smokes_or_drinks,
                        health_concerns, intake_signature, compliance_signature,
                        created_at, lang
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    data["first_name"], data["last_name"], data["full_name"],
                    data["email"], data.get("phone", ""),
                    data.get("dob", ""), data.get("weight", ""), data.get("height", ""),
                    data.get("pacemaker", False), data.get("conditions", False),
                    data.get("medications", False), data.get("procedures", False),
                    data.get("smokes", False), data.get("health_concerns", ""),
                    data.get("intake_signature", ""), data.get("compliance_signature", ""),
                    now, data.get("lang", "en"),
                ))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving: {e}")
        return False


# -----------------------------
# Translations
# -----------------------------
T = {
    "en": {
        "intake_title": "Scanner Intake Form",
        "personal_info": "Personal Information",
        "first_name": "First Name",
        "last_name": "Last Name",
        "email": "E-Mail for Results",
        "phone": "Phone Number",
        "dob": "Date of Birth (MM/DD/YYYY)",
        "weight": "Weight (kg)",
        "height": "Height (cm)",
        "medical": "Medical Briefing",
        "q_pacemaker": "Do you have a pacemaker?",
        "q_conditions": "Do you have any existing health conditions or diagnoses?",
        "q_medications": "Are you taking any medications or supplements?",
        "q_procedures": "Have you recently undergone any medical procedures or surgeries?",
        "q_smokes": "Do you smoke or consume alcohol regularly?",
        "additional": "Additional Information",
        "health_concerns": "What are your main health concerns or goals for this scan?",
        "signature": "Signature",
        "sign_here": "Sign below",
        "intake_consent": "I am aware that it is my duty to submit truthful information. I agree to the terms of service, and am aware that this scan is an alternative wellness tool and not meant for medical diagnosis.",
        "next_page": "Continue to Compliance Agreement →",
        "compliance_title": "Compliance and Agreement — Quantum Bio-Resonance Scanner",
        "compliance_sec1_title": "I. Acknowledgment of Intent and Scope of Use",
        "compliance_sec1": "By signing this agreement, the Buyer affirms that the Quantum Bio-Resonance Scanner is acquired for personal wellness monitoring, experimental insight, or private holistic practices, and not as a substitute for certified medical diagnostics, prescriptions, or emergency care. Buyer understands that no claims are made by the seller or by Vital Health Global LLC regarding the cure, treatment, or diagnosis of any disease.",
        "compliance_sec2_title": "II. Non-Medical Device Declaration",
        "compliance_sec2": "The Buyer fully understands that the product is not classified as a Class I, II, or III medical device under any FDA, COFEPRIS, EMA, or global equivalent medical regulation framework. The scanner operates using proprietary algorithms and frequency analytics that fall under the category of biofeedback wellness tools, and its outcomes are to be interpreted subjectively and with informed discretion.",
        "compliance_sec3_title": "III. Responsibility and Liability",
        "compliance_sec3": "The Buyer releases the Seller, Vital Health Global LLC, its affiliates, and technology partners from any and all liability arising from misuse, misinterpretation, or misrepresentation of the scanner's outputs. Buyer agrees not to hold Vital Health or its partners accountable for any wellness decisions, supplement intake, lifestyle changes, or therapeutic pathways chosen post-scan.",
        "compliance_sec4_title": "IV. Use Certification and Intellectual Handling",
        "compliance_sec4": "The Buyer acknowledges that the device is best operated by individuals trained in frequency interpretation, energy resonance frameworks, or allied biofield disciplines. Buyer further agrees to abstain from reselling the device with medical promises or unsubstantiated claims and understands that any form of public advertising must state clearly: 'Not a medical device.'",
        "compliance_sec5_title": "V. Data and Privacy Note",
        "compliance_sec5": "Any personal scan data collected remains under the sole custodianship of the Buyer unless explicitly shared. The scanner may log session data internally for performance tracking, but this information is never uploaded, harvested, or sold without direct consent.",
        "compliance_sec6_title": "VI. Final Clause — Informed Autonomy",
        "compliance_sec6": "The Buyer declares full understanding that this device is a tool for exploration, not a determinant of truth, and enters this agreement with conscious autonomy and sovereign discernment. Vital Health Global LLC disclaims any liability arising from independent usage or interpretations not aligned with its official literature or training guidelines.",
        "compliance_sign": "By signing below, I agree to all terms above.",
        "submit": "Submit Intake Form",
        "success": "✅ Thank you! Your intake form has been submitted successfully. Your representative will be with you shortly.",
        "required": "Please fill in your first name, last name, and email.",
        "sig_required": "Please sign both the intake form and the compliance agreement.",
        "back": "← Back to Intake Form",
        "lang_toggle": "ES",
        "today": "Today's Date",
    },
    "es": {
        "intake_title": "Formulario de Ingreso del Escáner",
        "personal_info": "Información Personal",
        "first_name": "Nombre",
        "last_name": "Apellido",
        "email": "Correo Electrónico para Resultados",
        "phone": "Número de Teléfono",
        "dob": "Fecha de Nacimiento (MM/DD/AAAA)",
        "weight": "Peso (kg)",
        "height": "Altura (cm)",
        "medical": "Información Médica",
        "q_pacemaker": "¿Tiene un marcapasos?",
        "q_conditions": "¿Tiene alguna condición de salud o diagnóstico existente?",
        "q_medications": "¿Está tomando algún medicamento o suplemento?",
        "q_procedures": "¿Se ha sometido recientemente a algún procedimiento médico o cirugía?",
        "q_smokes": "¿Fuma o consume alcohol regularmente?",
        "additional": "Información Adicional",
        "health_concerns": "¿Cuáles son sus principales preocupaciones de salud u objetivos para este escaneo?",
        "signature": "Firma",
        "sign_here": "Firme abajo",
        "intake_consent": "Soy consciente de que es mi deber enviar información veraz. Acepto los términos de servicio y soy consciente de que este escaneo es una herramienta de bienestar alternativa y no está destinado para diagnóstico médico.",
        "next_page": "Continuar al Acuerdo de Cumplimiento →",
        "compliance_title": "Acuerdo de Cumplimiento — Escáner de Bio-Resonancia Cuántica",
        "compliance_sec1_title": "I. Reconocimiento de Intención y Alcance de Uso",
        "compliance_sec1": "Al firmar este acuerdo, el Comprador afirma que el Escáner de Bio-Resonancia Cuántica se adquiere para monitoreo personal de bienestar, perspectiva experimental o prácticas holísticas privadas, y no como sustituto de diagnósticos médicos certificados, prescripciones o atención de emergencia.",
        "compliance_sec2_title": "II. Declaración de Dispositivo No Médico",
        "compliance_sec2": "El Comprador entiende completamente que el producto no está clasificado como dispositivo médico Clase I, II o III bajo ningún marco regulatorio médico equivalente de la FDA, COFEPRIS, EMA o global.",
        "compliance_sec3_title": "III. Responsabilidad y Obligación",
        "compliance_sec3": "El Comprador libera al Vendedor, Vital Health Global LLC, sus afiliados y socios tecnológicos de toda responsabilidad derivada del mal uso, mala interpretación o tergiversación de los resultados del escáner.",
        "compliance_sec4_title": "IV. Certificación de Uso y Manejo Intelectual",
        "compliance_sec4": "El Comprador reconoce que el dispositivo es mejor operado por personas capacitadas en interpretación de frecuencias, marcos de resonancia energética o disciplinas de biocampo aliadas.",
        "compliance_sec5_title": "V. Nota de Datos y Privacidad",
        "compliance_sec5": "Cualquier dato personal de escaneo recopilado permanece bajo la custodia exclusiva del Comprador a menos que se comparta explícitamente.",
        "compliance_sec6_title": "VI. Cláusula Final — Autonomía Informada",
        "compliance_sec6": "El Comprador declara plena comprensión de que este dispositivo es una herramienta de exploración, no un determinante de verdad, y entra en este acuerdo con autonomía consciente y discernimiento soberano.",
        "compliance_sign": "Al firmar abajo, acepto todos los términos anteriores.",
        "submit": "Enviar Formulario",
        "success": "✅ ¡Gracias! Su formulario ha sido enviado exitosamente. Su representante estará con usted en breve.",
        "required": "Por favor complete su nombre, apellido y correo electrónico.",
        "sig_required": "Por favor firme tanto el formulario de ingreso como el acuerdo de cumplimiento.",
        "back": "← Volver al Formulario",
        "lang_toggle": "EN",
        "today": "Fecha de Hoy",
    },
}


def t(key: str) -> str:
    lang = st.session_state.get("lang", "en")
    return T.get(lang, T["en"]).get(key, key)


# -----------------------------
# Signature helper
# -----------------------------
def _has_signature(canvas_result) -> bool:
    if canvas_result is None or canvas_result.image_data is None:
        return False
    import numpy as np
    alpha = canvas_result.image_data[:, :, 3]
    return int(alpha.sum()) > 1000


def _signature_to_base64(canvas_result) -> str:
    if canvas_result is None or canvas_result.image_data is None:
        return ""
    from PIL import Image
    import io
    img = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# -----------------------------
# Page 1: Intake Form
# -----------------------------
def render_intake_page():
    # Language toggle
    lang = st.session_state.get("lang", "en")
    if st.button(t("lang_toggle"), key="lang_btn"):
        st.session_state["lang"] = "es" if lang == "en" else "en"
        st.rerun()

    if LOGO_PATH.exists():
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.image(str(LOGO_PATH), width=220)

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    st.markdown(f'<p class="intake-title">🩺 {t("intake_title")}</p>', unsafe_allow_html=True)

    # Personal Information
    st.markdown(f'<p class="section-header">{t("personal_info")}</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        first_name = st.text_input(t("first_name"), key="i_first")
    with c2:
        last_name = st.text_input(t("last_name"), key="i_last")

    email = st.text_input(t("email"), key="i_email")

    c3, c4 = st.columns(2)
    with c3:
        phone = st.text_input(t("phone"), key="i_phone")
    with c4:
        dob = st.text_input(t("dob"), placeholder="MM/DD/YYYY", key="i_dob")

    # Height: Feet + Inches → auto-convert to cm
    _is_es = st.session_state.get("lang") == "es"
    st.markdown(f'**{"Altura" if _is_es else "Height"}**')
    h1, h2, h3 = st.columns(3)
    with h1:
        feet = st.number_input("Pies" if _is_es else "Feet", min_value=0, max_value=8, step=1, value=0, key="i_feet")
    with h2:
        inches = st.number_input("Pulgadas" if _is_es else "Inches", min_value=0.0, max_value=11.99, step=0.5, value=0.0, key="i_inches")
    with h3:
        total_inches = (feet * 12) + inches
        height_cm = round(total_inches * 2.54, 1)
        if total_inches > 0:
            st.metric("cm", f"{height_cm}")

    # Weight: Pounds → auto-convert to kg
    st.markdown(f'**{"Peso" if _is_es else "Weight"}**')
    w1, w2 = st.columns(2)
    with w1:
        pounds = st.number_input("Libras (lbs)" if _is_es else "Pounds (lbs)", min_value=0.0, step=0.5, value=0.0, key="i_pounds")
    with w2:
        weight_kg = round(pounds * 0.45359237, 1)
        if pounds > 0:
            st.metric("kg", f"{weight_kg}")

    st.divider()

    # Medical Briefing — Yes/No radio buttons
    _yes = "Sí" if _is_es else "Yes"
    _no = "No"
    st.markdown(f'<p class="section-header">{t("medical")}</p>', unsafe_allow_html=True)
    pacemaker = st.radio(f"1. {t('q_pacemaker')}", [_no, _yes], horizontal=True, key="i_pace") == _yes
    conditions = st.radio(f"2. {t('q_conditions')}", [_no, _yes], horizontal=True, key="i_cond") == _yes
    medications = st.radio(f"3. {t('q_medications')}", [_no, _yes], horizontal=True, key="i_meds") == _yes
    procedures = st.radio(f"4. {t('q_procedures')}", [_no, _yes], horizontal=True, key="i_proc") == _yes
    smokes = st.radio(f"5. {t('q_smokes')}", [_no, _yes], horizontal=True, key="i_smoke") == _yes

    st.divider()

    # Additional Information
    st.markdown(f'<p class="section-header">{t("additional")}</p>', unsafe_allow_html=True)
    health_concerns = st.text_area(t("health_concerns"), key="i_concerns", height=120)

    st.divider()

    # Consent + Signature
    st.markdown(f'<div class="compliance-text">{t("intake_consent")}</div>', unsafe_allow_html=True)

    st.markdown(f'<p class="sig-label">{t("signature")} — {t("sign_here")}</p>', unsafe_allow_html=True)
    intake_sig = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",
        stroke_width=2,
        stroke_color="#1b1b1b",
        background_color="#ffffff",
        height=120,
        width=400,
        drawing_mode="freedraw",
        key="intake_sig_canvas",
    )

    st.caption(f"{t('today')}: {datetime.now().strftime('%B %d, %Y')}")

    st.divider()

    if st.button(t("next_page"), type="primary", use_container_width=True, key="next_btn"):
        if not first_name.strip() or not last_name.strip() or not email.strip():
            st.error(t("required"))
        elif not _has_signature(intake_sig):
            st.warning(t("sig_required"))
        else:
            st.session_state["intake_data"] = {
                "first_name": first_name.strip().title(),
                "last_name": last_name.strip().title(),
                "full_name": f"{first_name.strip().title()} {last_name.strip().title()}",
                "email": email.strip(),
                "phone": phone.strip(),
                "dob": dob.strip(),
                "weight": str(weight_kg),
                "height": str(height_cm),
                "pacemaker": pacemaker,
                "conditions": conditions,
                "medications": medications,
                "procedures": procedures,
                "smokes": smokes,
                "health_concerns": health_concerns.strip(),
                "intake_signature": _signature_to_base64(intake_sig),
                "lang": st.session_state.get("lang", "en"),
            }
            st.session_state["page"] = "compliance"
            st.rerun()


# -----------------------------
# Page 2: Compliance Agreement
# -----------------------------
def render_compliance_page():
    if st.button(t("back"), key="comp_back"):
        st.session_state["page"] = "intake"
        st.rerun()

    if LOGO_PATH.exists():
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.image(str(LOGO_PATH), width=220)

    st.markdown(f'<p class="section-header">📋 {t("compliance_title")}</p>', unsafe_allow_html=True)

    # Sections
    for i in range(1, 7):
        title_key = f"compliance_sec{i}_title"
        text_key = f"compliance_sec{i}"
        st.markdown(f"**{t(title_key)}**")
        st.markdown(f'<div class="compliance-text">{t(text_key)}</div>', unsafe_allow_html=True)

    st.divider()

    st.markdown(f'<div class="compliance-text"><strong>{t("compliance_sign")}</strong></div>', unsafe_allow_html=True)

    st.markdown(f'<p class="sig-label">{t("signature")} — {t("sign_here")}</p>', unsafe_allow_html=True)
    compliance_sig = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",
        stroke_width=2,
        stroke_color="#1b1b1b",
        background_color="#ffffff",
        height=120,
        width=400,
        drawing_mode="freedraw",
        key="compliance_sig_canvas",
    )

    st.caption(f"{t('today')}: {datetime.now().strftime('%B %d, %Y')}")

    st.divider()

    if st.button(t("submit"), type="primary", use_container_width=True, key="submit_btn"):
        if not _has_signature(compliance_sig):
            st.warning(t("sig_required"))
        else:
            data = st.session_state.get("intake_data", {})
            data["compliance_signature"] = _signature_to_base64(compliance_sig)
            if save_intake(data):
                st.session_state["page"] = "success"
                st.rerun()


# -----------------------------
# Success Page
# -----------------------------
def render_success_page():
    if LOGO_PATH.exists():
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.image(str(LOGO_PATH), width=220)
    st.success(t("success"))
    st.balloons()


# -----------------------------
# Distributor: Search & Claim Intakes
# -----------------------------
def _get_distributor_password() -> str:
    pw = os.environ.get("DISTRIBUTOR_PASSWORD", "")
    if not pw:
        try:
            pw = st.secrets["DISTRIBUTOR_PASSWORD"]
        except Exception:
            pass
    return pw


def _search_unclaimed(name_query: str) -> list:
    if not DATABASE_URL:
        return []
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        q = f"%{name_query.strip().lower()}%"
        with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, first_name, last_name, email, phone,
                           date_of_birth, weight_kg, height_cm,
                           has_pacemaker, has_conditions, takes_medications,
                           recent_procedures, smokes_or_drinks,
                           health_concerns, created_at, lang
                    FROM client_intake
                    WHERE claimed_by IS NULL
                      AND (LOWER(first_name) LIKE %s
                           OR LOWER(last_name) LIKE %s
                           OR LOWER(first_name || ' ' || last_name) LIKE %s)
                    ORDER BY created_at DESC
                """, (q, q, q))
                return cur.fetchall()
    except Exception as e:
        st.error(f"DB error: {e}")
        return []


def _fetch_all_unclaimed() -> list:
    if not DATABASE_URL:
        return []
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, first_name, last_name, email, phone,
                           date_of_birth, weight_kg, height_cm,
                           has_pacemaker, has_conditions, takes_medications,
                           recent_procedures, smokes_or_drinks,
                           health_concerns, created_at, lang
                    FROM client_intake
                    WHERE claimed_by IS NULL
                    ORDER BY created_at DESC
                """)
                return cur.fetchall()
    except Exception as e:
        st.error(f"DB error: {e}")
        return []


def _claim_intake(intake_id: int, distributor_name: str) -> bool:
    if not DATABASE_URL:
        return False
    try:
        import psycopg2
        now = datetime.now(timezone.utc).isoformat()
        conn = psycopg2.connect(DATABASE_URL)
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE client_intake
                SET claimed_by = %s, claimed_at = %s
                WHERE id = %s AND claimed_by IS NULL
            """, (distributor_name, now, intake_id))
            conn.commit()
            updated = cur.rowcount
            cur.close()
            conn.close()
            return updated > 0
        except Exception:
            conn.rollback()
            conn.close()
            raise
    except Exception as e:
        st.error(f"Claim error: {e}")
        return False


def _render_intake_card(row, distributor_name: str):
    yn = lambda v: "Yes" if v else "No"
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"📧 Email: {row.get('email', '—')}")
        st.write(f"📞 Phone: {row.get('phone', '—')}")
        st.write(f"🎂 DOB: {row.get('date_of_birth', '—')}")
        st.write(f"📏 Height: {row.get('height_cm', '—')} cm")
        st.write(f"⚖️ Weight: {row.get('weight_kg', '—')} kg")
    with c2:
        st.write(f"1. Pacemaker: {yn(row.get('has_pacemaker'))}")
        st.write(f"2. Health conditions: {yn(row.get('has_conditions'))}")
        st.write(f"3. Medications: {yn(row.get('takes_medications'))}")
        st.write(f"4. Recent procedures: {yn(row.get('recent_procedures'))}")
        st.write(f"5. Smokes/Drinks: {yn(row.get('smokes_or_drinks'))}")
    concerns = row.get('health_concerns', '').strip()
    if concerns:
        st.write(f"💬 Health concerns: {concerns}")
    st.caption(f"Submitted: {row.get('created_at', '—')[:16]}")

    btn_key = f"claim_{row['id']}"
    if st.button(f"✅ Claim {row['first_name']} {row['last_name']}", key=btn_key, type="primary"):
        if _claim_intake(row['id'], distributor_name):
            st.session_state["claimed_client"] = row
            st.rerun()
        else:
            st.error("Could not claim. It may have already been claimed.")


def render_distributor_page():
    if LOGO_PATH.exists():
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.image(str(LOGO_PATH), width=220)

    st.markdown('<p class="section-header">📋 Distributor — Client Intake Lookup</p>', unsafe_allow_html=True)

    dist_pw = _get_distributor_password()
    if not dist_pw:
        st.error("Distributor access not configured.")
        return

    # Password gate
    if not st.session_state.get("dist_authenticated"):
        pw = st.text_input("Distributor Password", type="password", key="dist_pw_input")
        if st.button("Login", type="primary", key="dist_login_btn"):
            if pw == dist_pw:
                st.session_state["dist_authenticated"] = True
                st.rerun()
            else:
                st.error("Wrong password.")
        return

    # Ask for distributor name (for claiming)
    if not st.session_state.get("dist_name"):
        name = st.text_input("Your Name (Distributor)", key="dist_name_input")
        if st.button("Continue", type="primary", key="dist_name_btn"):
            if name.strip():
                st.session_state["dist_name"] = name.strip()
                st.rerun()
            else:
                st.error("Please enter your name.")
        return

    distributor_name = st.session_state["dist_name"]
    st.caption(f"Logged in as: {distributor_name}")

    # Show claimed client confirmation
    claimed = st.session_state.get("claimed_client")
    if claimed:
        yn = lambda v: "Yes" if v else "No"
        st.success(f"✅ Claimed: {claimed['first_name']} {claimed['last_name']}")
        st.balloons()
        st.markdown('<p class="section-header">Client Details</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"📧 Email: {claimed.get('email', '—')}")
            st.write(f"📞 Phone: {claimed.get('phone', '—')}")
            st.write(f"🎂 DOB: {claimed.get('date_of_birth', '—')}")
            st.write(f"📏 Height: {claimed.get('height_cm', '—')} cm")
            st.write(f"⚖️ Weight: {claimed.get('weight_kg', '—')} kg")
        with c2:
            st.write(f"1. Pacemaker: {yn(claimed.get('has_pacemaker'))}")
            st.write(f"2. Health conditions: {yn(claimed.get('has_conditions'))}")
            st.write(f"3. Medications: {yn(claimed.get('takes_medications'))}")
            st.write(f"4. Recent procedures: {yn(claimed.get('recent_procedures'))}")
            st.write(f"5. Smokes/Drinks: {yn(claimed.get('smokes_or_drinks'))}")
        concerns = claimed.get('health_concerns', '').strip()
        if concerns:
            st.write(f"💬 Health concerns: {concerns}")
        st.divider()
        if st.button("🔍 Search Another Client", type="primary", key="search_another"):
            st.session_state.pop("claimed_client", None)
            st.rerun()
        return

    # Search
    search = st.text_input("🔍 Search client by name", key="dist_search")

    col_search, col_all = st.columns(2)
    with col_search:
        search_clicked = st.button("Search", type="primary", use_container_width=True, key="dist_search_btn")
    with col_all:
        show_all = st.button("Show All Unclaimed", use_container_width=True, key="dist_all_btn")

    rows = []
    if search_clicked and search.strip():
        rows = _search_unclaimed(search)
        if not rows:
            st.warning(f"No unclaimed intakes found for \"{search}\"")
    elif show_all:
        rows = _fetch_all_unclaimed()
        if not rows:
            st.info("No unclaimed intakes.")

    if rows:
        st.caption(f"{len(rows)} result(s)")
        for row in rows:
            label = f"**{row['first_name']} {row['last_name']}** — {row['email']} — {row['created_at'][:10]}"
            with st.expander(label):
                _render_intake_card(row, distributor_name)


# -----------------------------
# Main
# -----------------------------
def main():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    if "page" not in st.session_state:
        st.session_state["page"] = "intake"

    # Check for ?view=intakes in URL
    params = st.query_params
    if params.get("view") == "intakes":
        render_distributor_page()
        return

    page = st.session_state.get("page", "intake")

    if page == "compliance":
        render_compliance_page()
    elif page == "success":
        render_success_page()
    else:
        render_intake_page()


if __name__ == "__main__":
    main()
