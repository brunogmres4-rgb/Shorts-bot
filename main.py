import streamlit as st
import os
import requests
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from supabase import create_client
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# Configuración de la página
st.set_page_config(
    page_title="Shorts Studio | Cloud Pipeline", 
    layout="centered"
)

# Estilos CSS avanzados con diseño SaaS y corrección de colores de texto
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Forzar que todos los textos, títulos y etiquetas sean oscuros y legibles */
    h1, h2, h3, h4, h5, h6, span, label, .stMarkdown, p {
        color: #0f172a !important;
    }
    
    .header-subtitle, p[style*="color: #64748b"] {
        color: #64748b !important;
    }
    
    .icon-inline {
        display: inline-flex;
        align-self: center;
        vertical-align: middle;
        margin-right: 8px;
        width: 20px;
        height: 20px;
        stroke: currentColor;
        stroke-width: 2;
        stroke-linecap: round;
        stroke-linejoin: round;
        fill: none;
    }

    .header-title {
        font-size: 2.25rem;
        font-weight: 700;
        color: #0f172a !important;
        letter-spacing: -0.03em;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 6px;
    }

    .header-subtitle {
        color: #64748b !important;
        font-size: 1rem;
        margin-bottom: 2.5rem;
    }

    .stButton>button {
        width: 100%;
        background-color: #0f172a;
        color: #ffffff !important;
        border: 1px solid #0f172a;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease-in-out;
    }

    .stButton>button:hover {
        background-color: #1e293b;
        border-color: #1e293b;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.12);
    }

    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        background-color: #ffffff;
        color: #0f172a !important;
        font-size: 0.95rem;
        padding: 0.75rem;
    }

    .studio-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.03);
        margin-bottom: 1.5rem;
    }
    
    .status-box {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        padding: 1rem 1.25rem;
        border-radius: 10px;
        color: #334155 !important;
        font-weight: 500;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Iconos SVG
SVG_ZAP = '<svg class="icon-inline" style="width:32px;height:32px;color:#0f172a;" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>'
SVG_VIDEO = '<svg class="icon-inline" viewBox="0 0 24 24"><path d="m22 8-6 4 6 4V8Z"></path><rect width="14" height="12" x="2" y="6" rx="2" ry="2"></rect></svg>'
SVG_SHIELD = '<svg class="icon-inline" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
SVG_SPINNER = '<svg class="icon-inline" style="animation: spin 1.5s linear infinite;" viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>'

# Credenciales (Secrets o Session)
PIXABAY_KEY = st.secrets.get("PIXABAY_KEY", st.session_state.get('PIXABAY_KEY', ''))
SUPABASE_URL = st.secrets.get("SUPABASE_URL", st.session_state.get('SUPABASE_URL', ''))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", st.session_state.get('SUPABASE_KEY', ''))
YT_CLIENT_ID = st.secrets.get("YT_CLIENT_ID", st.session_state.get('YT_CLIENT_ID', ''))
YT_CLIENT_SECRET = st.secrets.get("YT_CLIENT_SECRET", st.session_state.get('YT_CLIENT_SECRET', ''))
YT_REFRESH_TOKEN = st.secrets.get("YT_REFRESH_TOKEN", st.session_state.get('YT_REFRESH_TOKEN', ''))

st.markdown(f'<div class="header-title">{SVG_ZAP} Shorts Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Pipeline automatizado para generación y publicación de YouTube Shorts.</div>', unsafe_allow_html=True)

tab_app, tab_config = st.tabs(["Generador", "Configuración"])

with tab_app:
    st.markdown('<div class="studio-card">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="font-size:1.15rem; color:#0f172a; margin-bottom:1.2rem; display:flex; align-items:center;">{SVG_VIDEO} Nuevo Guion de Producción</h3>', unsafe_allow_html=True)
    
    guion = st.text_area(
        "Guion narrativo (40-50 segundos):", 
        value=st.session_state.get('draft_guion', ''),
        placeholder="Escribe el guion técnico del vídeo...", 
        height=150,
        key="input_guion"
    )
    
    busqueda_broll = st.text_input(
        "Concepto visual B-roll (Pixabay):", 
        value=st.session_state.get('draft_broll', 'dark technology abstract'),
        placeholder="Ej: servers, coding, artificial intelligence...",
        key="input_broll"
    )
    
    titulo_short = st.text_input(
        "Título del YouTube Short:",
        value=st.session_state.get('draft_title', 'Curiosidades Tecnológicas #Shorts'),
        key="input_title"
    )
    
    st.session_state['draft_guion'] = guion
    st.session_state['draft_broll'] = busqueda_broll
    st.session_state['draft_title'] = titulo_short
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    if st.button("Ejecutar Pipeline Cloud y Publicar"):
        if not guion:
            st.warning("Por favor, introduce un guion antes de comenzar.")
        elif not PIXABAY_KEY or not SUPABASE_URL:
            st.error("Faltan credenciales esenciales de Pixabay o Supabase.")
        else:
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # 1. Edge-TTS
                status_placeholder.markdown(f'<div class="status-box">{SVG_SPINNER} Sintetizando voz en off (Edge-TTS)...</div>', unsafe_allow_html=True)
                progress_bar.progress(15)
                async def make_audio():
                    communicate = edge_tts.Communicate(guion, "es-ES-AlvaroNeural")
                    await communicate.save("audio.mp3")
                asyncio.run(make_audio())
                
                # 2. Pixabay API
                status_placeholder.markdown(f'<div class="status-box">{SVG_SPINNER} Descargando clips B-roll desde Pixabay...</div>', unsafe_allow_html=True)
                progress_bar.progress(35)
                pixabay_url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={busqueda_broll}&orientation=vertical&per_page=3"
                res = requests.get(pixabay_url).json()
                
                video_files = []
                hits = res.get('hits', [])
                for i, video in enumerate(hits[:3]):
                    video_url = video['videos']['medium']['url']
                    v_data = requests.get(video_url).content
                    v_path = f"clip_{i}.mp4"
                    with open(v_path, "wb") as f:
                        f.write(v_data)
                    video_files.append(VideoFileClip(v_path).subclip(0, 5))
                
                # 3. Composición con MoviePy
                status_placeholder.markdown(f'<div class="status-box">{SVG_SPINNER} Renderizando vídeo final...</div>', unsafe_allow_html=True)
                progress_bar.progress(55)
                audio_clip = AudioFileClip("audio.mp3")
                final_clip = concatenate_videoclips(video_files, method="compose").set_duration(audio_clip.duration)
                final_clip = final_clip.set_audio(audio_clip)
                final_clip.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")
                
                # 4. Supabase Storage (Respaldo en la nube)
                status_placeholder.markdown(f'<div class="status-box">{SVG_SPINNER} Subiendo recurso a Supabase Storage...</div>', unsafe_allow_html=True)
                progress_bar.progress(75)
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                with open("output.mp4", "rb") as f:
                    supabase.storage.from_("videos").upload("short_temp.mp4", f)
                
                # 5. Publicación en YouTube Shorts via API
                status_placeholder.markdown(f'<div class="status-box">{SVG_SPINNER} Publicando Short en YouTube...</div>', unsafe_allow_html=True)
                progress_bar.progress(90)
                
                if YT_CLIENT_ID and YT_CLIENT_SECRET and YT_REFRESH_TOKEN:
                    creds = Credentials(
                        None,
                        refresh_token=YT_REFRESH_TOKEN,
                        client_id=YT_CLIENT_ID,
                        client_secret=YT_CLIENT_SECRET,
                        token_uri="https://oauth2.googleapis.com/token"
                    )
                    youtube = build("youtube", "v3", credentials=creds)
                    
                    body = {
                        "snippet": {
                            "title": titulo_short,
                            "description": f"{guion}\n\n#Shorts #Tech",
                            "tags": ["shorts", "tecnologia"],
                            "categoryId": "28"
                        },
                        "status": {
                            "privacyStatus": "public",
                            "selfDeclaredMadeForKids": False
                        }
                    }
                    
                    media = MediaFileUpload("output.mp4", chunksize=-1, resumable=True)
                    request = youtube.videos().insert(
                        part="snippet,status",
                        body=body,
                        media_body=media
                    )
                    response = request.execute()
                
                # 6. Purga de archivos temporales
                progress_bar.progress(98)
                supabase.storage.from_("videos").remove(["short_temp.mp4"])
                progress_bar.progress(100)
                status_placeholder.empty()
                
                if os.path.exists("audio.mp3"): os.remove("audio.mp3")
                if os.path.exists("output.mp4"): os.remove("output.mp4")
                for i in range(len(video_files)):
                    if os.path.exists(f"clip_{i}.mp4"): os.remove(f"clip_{i}.mp4")
                    
                st.success("✨ ¡Pipeline ejecutado y vídeo publicado con éxito en YouTube Shorts!")
                
            except Exception as e:
                progress_bar.empty()
                status_placeholder.empty()
                st.error(f"Error crítico en el pipeline: {e}")
                
    st.markdown('</div>', unsafe_allow_html=True)

# --- PESTAÑA CONFIGURACIÓN ---
with tab_config:
    st.markdown('<div class="studio-card">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="font-size:1.15rem; color:#0f172a; margin-bottom:0.5rem; display:flex; align-items:center;">{SVG_SHIELD} Credenciales de API</h3>', unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 0.9rem; margin-bottom:1.5rem;'>Configura las claves de Pixabay, Supabase y YouTube.</p>", unsafe_allow_html=True)
    
    pixabay_key_input = st.text_input("Pixabay API Key", type="password", value=PIXABAY_KEY)
    supabase_url_input = st.text_input("Supabase Project URL", value=SUPABASE_URL)
    supabase_key_input = st.text_input("Supabase Service Key", type="password", value=SUPABASE_KEY)
    yt_client_id_input = st.text_input("YouTube Client ID", value=YT_CLIENT_ID)
    yt_client_secret_input = st.text_input("YouTube Client Secret", type="password", value=YT_CLIENT_SECRET)
    yt_refresh_token_input = st.text_input("YouTube Refresh Token", type="password", value=YT_REFRESH_TOKEN)
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    if st.button("Guardar Ajustes de Sesión"):
        st.session_state['PIXABAY_KEY'] = pixabay_key_input
        st.session_state['SUPABASE_URL'] = supabase_url_input
        st.session_state['SUPABASE_KEY'] = supabase_key_input
        st.session_state['YT_CLIENT_ID'] = yt_client_id_input
        st.session_state['YT_CLIENT_SECRET'] = yt_client_secret_input
        st.session_state['YT_REFRESH_TOKEN'] = yt_refresh_token_input
        st.success("¡Ajustes guardados correctamente en la sesión!")
        
    st.markdown('</div>', unsafe_allow_html=True)
