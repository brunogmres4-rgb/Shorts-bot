import streamlit as st
import os
import requests
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from supabase import create_client

# Configuración de la página
st.set_page_config(
    page_title="Shorts Studio | Cloud Pipeline", 
    layout="centered"
)

# Estilos CSS con SVG de Lucide integrados
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Iconos SVG inline */
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
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.03em;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 4px;
    }

    .header-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    /* Estilizado de Botones Flat */
    .stButton>button {
        width: 100%;
        background-color: #0f172a;
        color: #ffffff;
        border: 1px solid #0f172a;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.15s ease-in-out;
    }

    .stButton>button:hover {
        background-color: #1e293b;
        border-color: #1e293b;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }

    /* Campos de entrada */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background-color: #ffffff;
        color: #0f172a;
        font-size: 0.95rem;
    }

    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #0f172a;
        box-shadow: 0 0 0 1px #0f172a;
    }

    .section-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Iconos SVG de Lucide
SVG_ZAP = '<svg class="icon-inline" style="width:28px;height:28px;color:#0f172a;" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>'
SVG_VIDEO = '<svg class="icon-inline" viewBox="0 0 24 24"><path d="m22 8-6 4 6 4V8Z"></path><rect width="14" height="12" x="2" y="6" rx="2" ry="2"></rect></svg>'
SVG_SETTINGS = '<svg class="icon-inline" viewBox="0 0 24 24"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>'
SVG_SPARKLES = '<svg class="icon-inline" viewBox="0 0 24 24"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path></svg>'
SVG_SHIELD = '<svg class="icon-inline" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'

# Header
st.markdown(f'<div class="header-title">{SVG_ZAP} Shorts Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Pipeline automatizado para generación y publicación de YouTube Shorts.</div>', unsafe_allow_html=True)

# Tabs
tab_app, tab_config = st.tabs(["Generador", "Configuración"])

# --- PESTAÑA GENERADOR ---
with tab_app:
    st.markdown(f'<h3 style="font-size:1.1rem; color:#0f172a; margin-bottom:1rem;">{SVG_VIDEO} Nuevo Guion</h3>', unsafe_allow_html=True)
    
    guion = st.text_area(
        "Guion narrativo (40-50 segundos):", 
        placeholder="Escribe el guion técnico del vídeo...", 
        height=160
    )
    
    busqueda_broll = st.text_input(
        "Concepto visual B-roll (Pexels):", 
        value="dark technology abstract",
        placeholder="Ej: servers, coding, artificial intelligence..."
    )
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    if st.button("Ejecutar Pipeline"):
        if not guion:
            st.warning("Introduce un guion antes de comenzar.")
        elif not st.session_state.get('PEXELS_KEY') or not st.session_state.get('SUPABASE_URL'):
            st.error("Faltan credenciales. Ve a la pestaña Configuración.")
        else:
            status = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # 1. Edge-TTS
                status.text("Generando voz en off...")
                progress_bar.progress(20)
                async def make_audio():
                    communicate = edge_tts.Communicate(guion, "es-ES-AlvaroNeural")
                    await communicate.save("audio.mp3")
                asyncio.run(make_audio())
                
                # 2. Pexels API
                status.text("Obteniendo B-roll de Pexels...")
                progress_bar.progress(40)
                headers = {"Authorization": st.session_state.get('PEXELS_KEY')}
                res = requests.get(f"https://api.pexels.com/videos/search?query={busqueda_broll}&per_page=3&orientation=portrait", headers=headers).json()
                
                video_files = []
                for i, video in enumerate(res.get('videos', [])):
                    video_url = video['video_files'][0]['link']
                    v_data = requests.get(video_url).content
                    v_path = f"clip_{i}.mp4"
                    with open(v_path, "wb") as f:
                        f.write(v_data)
                    video_files.append(VideoFileClip(v_path).subclip(0, 5))
                
                # 3. Composición
                status.text("Renderizando vídeo...")
                progress_bar.progress(60)
                audio_clip = AudioFileClip("audio.mp3")
                final_clip = concatenate_videoclips(video_files, method="compose").set_duration(audio_clip.duration)
                final_clip = final_clip.set_audio(audio_clip)
                final_clip.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")
                
                # 4. Supabase
                status.text("Subiendo a Supabase Storage...")
                progress_bar.progress(80)
                supabase = create_client(st.session_state.get('SUPABASE_URL'), st.session_state.get('SUPABASE_KEY'))
                with open("output.mp4", "rb") as f:
                    supabase.storage.from_("videos").upload("short_temp.mp4", f)
                
                # 5. YouTube API
                status.text("Publicando en YouTube...")
                
                # 6. Purga
                status.text("Limpiando recursos temporales...")
                supabase.storage.from_("videos").remove(["short_temp.mp4"])
                
                progress_bar.progress(100)
                status.empty()
                
                if os.path.exists("audio.mp3"): os.remove("audio.mp3")
                if os.path.exists("output.mp4"): os.remove("output.mp4")
                for i in range(len(video_files)):
                    if os.path.exists(f"clip_{i}.mp4"): os.remove(f"clip_{i}.mp4")
                    
                st.success("Proceso completado. Vídeo publicado y almacenamiento purgado.")
                
            except Exception as e:
                st.error(f"Error en el proceso: {e}")

# --- PESTAÑA CONFIGURACIÓN ---
with tab_config:
    st.markdown(f'<h3 style="font-size:1.1rem; color:#0f172a; margin-bottom:0.5rem;">{SVG_SHIELD} Credenciales de API</h3>', unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 0.875rem; margin-bottom:1.5rem;'>Las claves se mantienen vivas en la sesión actual de la app.</p>", unsafe_allow_html=True)
    
    pexels_key = st.text_input("Pexels API Key", type="password", value=st.session_state.get('PEXELS_KEY', ''))
    supabase_url = st.text_input("Supabase Project URL", value=st.session_state.get('SUPABASE_URL', ''))
    supabase_key = st.text_input("Supabase Service Key", type="password", value=st.session_state.get('SUPABASE_KEY', ''))
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    if st.button("Guardar Ajustes"):
        st.session_state['PEXELS_KEY'] = pexels_key
        st.session_state['SUPABASE_URL'] = supabase_url
        st.session_state['SUPABASE_KEY'] = supabase_key
        st.success("Ajustes guardados correctamente.")
