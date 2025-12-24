import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional, List

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Planning Tool Pro", layout="centered")
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

# --- 2. AI LOGICA ---
def parse_email(text):
    prompt = f"Analyseer de mail en extraheer de klussen. Zoek ook naar lift-info:\n\n{text}"
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Je bent een logistiek planner. Wees compact en nauwkeurig."},
            {"role": "user", "content": prompt},
        ],
        response_format=PlanningOutput,
    )
    return response.choices[0].message.parsed

# --- 3. UI ---
st.title("🤖 Planning Assistent")

# Trengo koppeling
query_params = st.query_params
email_content = query_params.get("body", st.text_area("Plak mail tekst:", height=150))

if st.button("Genereer Overzicht", type="primary"):
    if email_content:
        result = parse_email(email_content)
        
        for i, job in enumerate(result.klussen):
            st.subheader(f"📍 Klus {i+1}: {job.locatie}")
            
            # --- SECTIE 1: MAIL REACTIE ---
            st.caption("1. REACTIE OP MAIL (Kopieer via knop rechtsboven)")
            job_data = job.model_dump()
            missing = [k.replace('_', ' ').capitalize() for k, v in job_data.items() if v == "Onbekend" and k != "lift_aanwezig"]
            
            if missing:
                missende_tekst = "\n".join([f"- {m}" for m in missing])
                mail_tekst = f"Hi Inkoop Office Projects,\n\nBedankt voor je aanvraag. Om de planning compleet te maken, hebben we nog een paar gegevens nodig:\n\n{missende_tekst}\n\nKun je deze informatie per mail aanvullen? Zodra we alles hebben, kunnen we de aanvraag verder in behandeling nemen."
            else:
                mail_tekst = "Hi Inkoop Office Projects,\n\nDank voor de aanvraag, wij gaan hem in de planning zetten. Over de invulling van de planning zullen wij snel meer delen.\n\nVriendelijke groet,\nPlanning Team"
            
            st.code(mail_tekst, language="text")

            # --- SECTIE 2: COMPACT OVERZICHT ---
            st.caption("2. KLUS INFORMATIE")
            overzicht_tekst = (
                f"Datum: {job.datum}\n"
                f"Starttijd: {job.starttijd}\n"
                f"Geschatte eindtijd: {job.eindtijd}\n"
                f"Werkzaamheden: {job.werkzaamheden}\n"
                f"Aantal Sjouwers: {job.aantal_sjouwers}\n"
                f"Locatie: {job.locatie}\n"
                f"Contactpersoon + tel: {job.contactpersoon_tel}\n"
                f"Materiaal: {job.materiaal}\n"
                f"PO Nummer: {job.po_nummer}"
            )
            st.code(overzicht_tekst, language="text")

            # --- SECTIE 3: BRIEFING ---
            st.caption("3. BRIEFING SJOUWERS")
            lift_tekst = "(Lift aanwezig)" if job.lift_aanwezig else "(Geen lift vermeld)"
            briefing_tekst = (
                f"Mannen, jullie gaan de klant ondersteunen met:\n\n"
                f"De werkzaamheden: {job.werkzaamheden}\n"
                f"Te sjouwen materiaal: {job.materiaal}\n"
                f"{lift_tekst}\n\n"
                f"De eindtijd is indicatief, de klant verwacht dat jullie rond {job.eindtijd} klaar zijn."
            )
            st.code(briefing_tekst, language="text")
            st.divider()
