import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional, List

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Trengo AI Parser", layout="wide")

# Haal je API key veilig op uit de instellingen (Stap 4)
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Definieer de datastructuur
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

class PlanningOutput(BaseModel):
    klussen: List[Job]

# --- 2. AI LOGICA ---
def parse_email(text):
    prompt = f"Extraheer alle klussen uit deze mail. Splits per dag of per locatie:\n\n{text}"
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Je bent een logistiek planner. Extraheer: Datum, Starttijd, Eindtijd, Werkzaamheden, Aantal Sjouwers, Locatie, Contactpersoon + tel nummer, Materiaal, PO Nummer."},
            {"role": "user", "content": prompt},
        ],
        response_format=PlanningOutput,
    )
    return response.choices[0].message.parsed

# --- 3. UI & TRENGO KOPPELING ---
st.write("### 🤖 Planning Assistent")

# Trengo stuurt de tekst van de mail mee in de URL
# We halen deze op met st.query_params
query_params = st.query_params
email_content = query_params.get("body", "")

if email_content:
    if st.button("Analyseer deze mail"):
        result = parse_email(email_content)
        
        all_missing = []
        for i, job in enumerate(result.klussen):
            with st.expander(f"Klus {i+1}", expanded=True):
                data = job.model_dump()
                st.table(data)
                
                # Check voor missende info
                missing = [k for k, v in data.items() if v == "Onbekend"]
                all_missing.extend(missing)
        
        if all_missing:
            st.warning("Informatie mist!")
            missende_str = ", ".join(list(set(all_missing)))
            reply = f"Hoi, bedankt voor de aanvraag! Ik mis nog: {missende_str}. Kun je dit sturen?"
            st.text_area("Concept antwoord:", value=reply)
else:
    st.info("Wachten op mail vanuit Trengo... (Of plak hieronder handmatig)")
    manual_text = st.text_area("Handmatige invoer:")
    if st.button("Analyseer Handmatig") and manual_text:
        # Zelfde logica als hierboven
        res = parse_email(manual_text)
        for job in res.klussen:
            st.table(job.model_dump())
