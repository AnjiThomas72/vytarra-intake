from __future__ import annotations
import os
import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# -----------------------------
# Config
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo.png"
DATABASE_URL = os.environ.get("DATABASE_URL", "")

st.set_page_config(
    page_title="VYTARRA™",
    page_icon="🟢",
    layout="wide",
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
    .landing-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 40px;
        margin: 20px auto;
        max-width: 500px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        text-align: center;
    }
    .intake-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px 40px;
        margin: 20px auto;
        max-width: 650px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
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
                        health_concerns, created_at, lang
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    data["first_name"], data["last_name"], data["full_name"],
                    data["email"], data.get("phone", ""),
                    data.get("dob", ""), data.get("weight", ""), data.get("height", ""),
                    data.get("pacemaker", False), data.get("conditions", False),
                    data.get("medications", False), data.get("procedures", False),
                    data.get("smokes", False), data.get("health_concerns", ""),
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
        "welcome": "Welcome to VYTARRA™",
        "choose": "How can we help you today?",
        "client_btn": "I'm a Client",
        "rep_btn": "I'm a Representative",
        "intake_title": "Scanner Intake Form",
        "personal_info": "Personal Information",
        "first_name": "First Name",
        "last_name": "Last Name",
        "email": "E-Mail for Results",
        "phone": "Phone Number",
        "dob": "Date of Birth",
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
        "consent": "I agree to the terms of service, and am aware that this scan is an alternative wellness tool and not meant for medical diagnosis.",
        "submit": "Submit Intake Form",
        "success": "Thank you! Your intake form has been submitted. Your representative will be with you shortly.",
        "required": "Please fill in your first name, last name, and email.",
        "consent_required": "Please agree to the terms of service.",
        "back": "← Back",
        "lang_toggle": "ES",
        "rep_redirect": "Representatives, please sign in at the main VYTARRA™ portal.",
    },
    "es": {
        "welcome": "Bienvenido a VYTARRA™",
        "choose": "¿Cómo podemos ayudarle hoy?",
        "client_btn": "Soy Cliente",
        "rep_btn": "Soy Representante",
        "intake_title": "Formulario de Ingreso del Escáner",
        "personal_info": "Información Personal",
        "first_name": "Nombre",
        "last_name": "Apellido",
        "email": "Correo Electrónico para Resultados",
        "phone": "Número de Teléfono",
        "dob": "Fecha de Nacimiento",
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
        "consent": "Acepto los términos de servicio y soy consciente de que este escaneo es una herramienta de bienestar alternativa y no está destinado para diagnóstico médico.",
        "submit": "Enviar Formulario",
        "success": "¡Gracias! Su formulario ha sido enviado. Su representante estará con usted en breve.",
        "required": "Por favor complete su nombre, apellido y correo electrónico.",
        "consent_required": "Por favor acepte los términos de servicio.",
        "back": "← Volver",
        "lang_toggle": "EN",
        "rep_redirect": "Representantes, por favor inicie sesión en el portal principal de VYTARRA™.",
    },
}


def t(key: str) -> str:
    lang = st.session_state.get("lang", "en")
    return T.get(lang, T["en"]).get(key, key)


# -----------------------------
# Pages
# -----------------------------
def show_logo():
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=250)


def render_landing():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="landing-card">', unsafe_allow_html=True)
        show_logo()
        st.markdown(f"### {t('welcome')}")
        st.markdown(f"<p style='color:#555;font-size:16px'>{t('choose')}</p>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"🩺 {t('client_btn')}", use_container_width=True, type="primary", key="landing_client"):
                st.session_state["page"] = "intake"
                st.rerun()
        with c2:
            if st.button(f"💼 {t('rep_btn')}", use_container_width=True, key="landing_rep"):
                st.session_state["page"] = "rep"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def render_rep_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="landing-card">', unsafe_allow_html=True)
        show_logo()
        st.markdown(f"### 💼 {t('rep_btn')}")
        st.info(t("rep_redirect"))
        if st.button(t("back"), key="rep_back"):
            st.session_state["page"] = "landing"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def render_intake_form():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        # Back button and language toggle
        b1, b2 = st.columns([1, 1])
        with b1:
            if st.button(t("back"), key="intake_back"):
                st.session_state["page"] = "landing"
                st.rerun()
        with b2:
            lang = st.session_state.get("lang", "en")
            if st.button(t("lang_toggle"), key="intake_lang"):
                st.session_state["lang"] = "es" if lang == "en" else "en"
                st.rerun()

        st.markdown('<div class="intake-card">', unsafe_allow_html=True)
        show_logo()
        st.markdown(f"### 🩺 {t('intake_title')}")

        # Personal Information
        st.markdown(f"**{t('personal_info')}**")
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input(t("first_name"), key="intake_first")
        with c2:
            last_name = st.text_input(t("last_name"), key="intake_last")

        email = st.text_input(t("email"), key="intake_email")

        c3, c4 = st.columns(2)
        with c3:
            phone = st.text_input(t("phone"), key="intake_phone")
        with c4:
            dob = st.text_input(t("dob"), placeholder="MM/DD/YYYY", key="intake_dob")

        c5, c6 = st.columns(2)
        with c5:
            weight = st.text_input(t("weight"), key="intake_weight")
        with c6:
            height = st.text_input(t("height"), key="intake_height")

        st.divider()

        # Medical Briefing
        st.markdown(f"**{t('medical')}**")
        pacemaker = st.checkbox(t("q_pacemaker"), key="intake_pacemaker")
        conditions = st.checkbox(t("q_conditions"), key="intake_conditions")
        medications = st.checkbox(t("q_medications"), key="intake_medications")
        procedures = st.checkbox(t("q_procedures"), key="intake_procedures")
        smokes = st.checkbox(t("q_smokes"), key="intake_smokes")

        st.divider()

        # Additional Information
        st.markdown(f"**{t('additional')}**")
        health_concerns = st.text_area(t("health_concerns"), key="intake_concerns", height=120)

        st.divider()

        # Consent
        consent = st.checkbox(t("consent"), key="intake_consent")

        # Submit
        if st.button(t("submit"), type="primary", use_container_width=True, key="intake_submit"):
            if not first_name.strip() or not last_name.strip() or not email.strip():
                st.error(t("required"))
            elif not consent:
                st.warning(t("consent_required"))
            else:
                data = {
                    "first_name": first_name.strip().title(),
                    "last_name": last_name.strip().title(),
                    "full_name": f"{first_name.strip().title()} {last_name.strip().title()}",
                    "email": email.strip(),
                    "phone": phone.strip(),
                    "dob": dob.strip(),
                    "weight": weight.strip(),
                    "height": height.strip(),
                    "pacemaker": pacemaker,
                    "conditions": conditions,
                    "medications": medications,
                    "procedures": procedures,
                    "smokes": smokes,
                    "health_concerns": health_concerns.strip(),
                    "lang": st.session_state.get("lang", "en"),
                }
                if save_intake(data):
                    st.success(t("success"))
                    st.balloons()

        st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------
# Main
# -----------------------------
def main():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    if "page" not in st.session_state:
        st.session_state["page"] = "landing"

    page = st.session_state.get("page", "landing")

    if page == "intake":
        render_intake_form()
    elif page == "rep":
        render_rep_page()
    else:
        render_landing()


if __name__ == "__main__":
    main()
