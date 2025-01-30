import os
import uuid
import gradio as gr
import assemblyai as aai
from translate import Translator
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

# Initialize AssemblyAI and ElevenLabs clients
aai.settings.api_key = assemblyai_api_key
client = ElevenLabs(api_key=elevenlabs_api_key)

# Use relative paths
script_dir = Path(__file__).parent  # Gets the directory where the script is running
images_dir = script_dir / "images"  # Points to the 'images' folder in your project

ru_img = Image.open(images_dir / "Russia.png").resize((80, 40))
tr_img = Image.open(images_dir / "Turkey.png").resize((80, 40))
sv_img = Image.open(images_dir / "Sweden.png").resize((80, 40))
de_img = Image.open(images_dir / "Germany.png").resize((80, 40))
es_img = Image.open(images_dir / "Spain.png").resize((80, 40))
ja_img = Image.open(images_dir / "Japanese.png").resize((80, 40))


def voice_to_voice(audio_file, progress=gr.Progress()):
    try:
        # Transcribe speech
        progress(0.1, desc="Transcribing audio...")
        transcript = transcribe_audio(audio_file)

        if transcript.status == aai.TranscriptStatus.error:
            raise gr.Error(f"Transcription failed: {transcript.error}")
        else:
            transcript_text = transcript.text

        # Translate text
        progress(0.4, desc="Translating text...")
        list_translations = translate_text(transcript_text)

        # Generate speech from text
        generated_audio_paths = []
        for i, translation in enumerate(list_translations):
            progress(0.5 + (i * 0.1), desc=f"Generating audio for {['Russian', 'Turkish', 'Swedish', 'German', 'Spanish', 'Japanese'][i]}...")
            translated_audio_file_name = text_to_speech(translation)
            path = Path(translated_audio_file_name)
            generated_audio_paths.append(path)

        return generated_audio_paths + list_translations

    except Exception as e:
        raise gr.Error(f"An error occurred: {str(e)}")

# Function to transcribe audio using AssemblyAI
def transcribe_audio(audio_file):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript

# Function to translate text
def translate_text(text: str) -> list:
    languages = ["ru", "tr", "sv", "de", "es", "ja"]
    list_translations = []
    for lan in languages:
        try:
            translator = Translator(from_lang="en", to_lang=lan)
            translation = translator.translate(text)
            list_translations.append(translation)
        except Exception as e:
            print(f"Translation to {lan} failed: {str(e)}")
            list_translations.append(f"Translation to {lan} failed.")
    return list_translations

# Function to generate speech
def text_to_speech(text: str) -> str:
    response = client.text_to_speech.convert(
        voice_id="Xb7hH8MSUJpSbSDYk0k2",  # Choose a voice on ElevenLabs dashboard and copy the id
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",  # Use the turbo model for low latency, for other languages use the `eleven_multilingual_v2`
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    save_file_path = f"{uuid.uuid4()}.mp3"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")

    # Return the path of the saved audio file
    return save_file_path

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## Record yourself in English and immediately receive voice translations.")
    
    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                show_download_button=True,
                waveform_options=gr.WaveformOptions(
                    waveform_color="#01C6FF",
                    waveform_progress_color="#0066B4",
                    skip_length=2,
                    show_controls=False,
                ),
            )
            with gr.Row():
                submit = gr.Button("Submit", variant="primary")
                btn = gr.ClearButton(audio_input, "Clear")

    with gr.Row():
        with gr.Group() as russian:
            gr.Markdown("### Russian 🇷🇺")
            gr.Image(ru_img)
            ru_output = gr.Audio(label="Russian", interactive=False)
            ru_text = gr.Markdown()

        with gr.Group() as turkish:
            gr.Markdown("### Turkish 🇹🇷")
            gr.Image(tr_img)
            tr_output = gr.Audio(label="Turkish", interactive=False)
            tr_text = gr.Markdown()

        with gr.Group() as swedish:
            gr.Markdown("### Swedish 🇸🇪")
            gr.Image(sv_img)
            sv_output = gr.Audio(label="Swedish", interactive=False)
            sv_text = gr.Markdown()

    with gr.Row():
        with gr.Group() as german:
            gr.Markdown("### German 🇩🇪")
            gr.Image(de_img)
            de_output = gr.Audio(label="German", interactive=False)
            de_text = gr.Markdown()

        with gr.Group() as spanish:
            gr.Markdown("### Spanish 🇪🇸")
            gr.Image(es_img)
            es_output = gr.Audio(label="Spanish", interactive=False)
            es_text = gr.Markdown()

        with gr.Group() as japanese:
            gr.Markdown("### Japanese 🇯🇵")
            gr.Image(ja_img)
            jp_output = gr.Audio(label="Japanese", interactive=False)
            jp_text = gr.Markdown()

    output_components = [ru_output, tr_output, sv_output, de_output, es_output, jp_output, ru_text, tr_text, sv_text, de_text, es_text, jp_text]
    submit.click(fn=voice_to_voice, inputs=audio_input, outputs=output_components, show_progress=True)

if __name__ == "__main__":
    demo.launch()