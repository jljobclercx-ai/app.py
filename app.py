import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional, List

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Planning Tool Pro", layout="wide")
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

class Job(BaseModel):
    datum: Optional[str] = "Onbekend"
    starttijd: Optional[str] = "Onbekend"
    eindtijd: Optional[str] = "Onbekend"
    werkzaamheden: Optional[str] = "Onbekend"
    aantal_sjouwers: Optional[str] = "Onbekend"
    locatie: Optional[str] = "Onbekend"
    contactpersoon_tel: Optional[str] = "Onbekend"
    materiaal: Optional[str] = "Onbekend"
    po_nummer: Optional[str] = "Onbekend"
    lift_aanwezig: Optional[bool] = False

class PlanningOutput(BaseModel):
    klussen: List[Job]

# --- 2. FUNCTIE ---
def parse_email(text):
    prompt = f"""
    Analyseer de mail en extraheer de klussen. 
    Let specifiek op of er een lift wordt genoemd.
    
    E-mail tekst:
    {text}
    """
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Je bent een logistiek expert. Extraheer data nauwkeurig. Vul 'Onbekend' in als iets mist."},
            {"role": "user", "content": prompt},
        ],
        response_format=PlanningOutput,
    )
    return response.choices[0].message.parsed

# --- 3. UI ---
st.title("🚛 Planning & Briefing Tool")

query_params = st.query_params
email_content = query_params.get("body", "")

if not email_content:
    email_content = st.text_area("Geen mail gevonden via Trengo. Plak hier handmatig:", height=200)

if email_content:
    if st.button("Genereer Output"):
        result = parse_email(email_content)
        
        for i, job in enumerate(result.klussen):
            st.divider()
            st.header(f"📍 Klus {i+1}: {job.locatie}")
            
            job_data = job.model_dump()
            missing_fields = [k.replace('_', ' ').capitalize() for k, v in job_data.items() if v == "Onbekend" and k != "lift_aanwezig"]

            # --- DEEL 1: REACTIE OP MAIL ---
            st.subheader("1. Reactie op mail")
            if missing_fields:
                missende_tekst = "\n".join([f"- {m}" for m in missing_fields])
                mail_tekst = (
                    f"Hi Inkoop Office Projects,\n\n"
                    f"Bedankt voor je aanvraag. Om de planning compleet te maken, hebben we nog een paar gegevens nodig:\n\n"
                    f"{missende_tekst}\n\n"
                    f"Kun je deze informatie per mail aanvullen? Zodra we alles hebben, kunnen we de aanvraag verder in behandeling nemen."
                )
            else:
                mail_tekst = (
                    "Hi Inkoop Office Projects,\n\n"
                    "Dank voor de aanvraag, wij gaan hem in de planning zetten. "
                    "Over de invulling van de planning zullen wij snel meer delen.\n\n"
                    "Vriendelijke groet,\n\nPlanning Team"
                )
            st.text_area("Kopieer klant-mail:", value=mail_tekst, height=200, key=f"mail_{i}")

            # --- DEEL 2: KLUS INFORMATIE ---
            st.subheader("2. Klus informatie")
            info_lijst = f"""
            **Datum:** {job.datum}
            **Starttijd:** {job.starttijd}
            **Geschatte eindtijd:** {job.eindtijd}
            **Werkzaamheden:** {job.werkzaamheden}
            **Aantal Sjouwers:** {job.aantal_sjouwers}
            **Locatie:** {job.locatie}
            **Contactpersoon + tel:** {job.contactpersoon_tel}
            **Materiaal:** {job.materiaal}
            **PO Nummer:** {job.po_nummer}
            """
            st.markdown(info_lijst)

            # --- DEEL 3: BRIEFING ---
            st.subheader("3. Briefing voor de mannen")
            lift_tekst = "(Lift aanwezig)" if job.lift_aanwezig else "(Geen lift vermeld)"
            
            briefing = (
                f"Mannen, jullie gaan de klant ondersteunen met:\n\n"
                f"**De werkzaamheden:** {job.werkzaamheden}\n"
                f"**Te sjouwen materiaal:** {job.materiaal}\n"
                f"{lift_tekst}\n\n"
                f"De eindtijd is indicatief, de klant verwacht dat jullie rond **{job.eindtijd}** klaar zijn."
            )
            st.info(briefing)
