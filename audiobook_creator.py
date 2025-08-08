#!/usr/bin/env python3
"""
Fish Audio Text-to-Speech Converter
Converts a text file to speech using Fish.audio's API with your cloned voice model.
"""

import os
import time
import re
from fish_audio_sdk import Session, TTSRequest

# Configuration
API_KEY = "your_api_key_here"  # Replace with your actual API key
MODEL_ID = "your_model_id_here"  # Replace with your cloned voice model ID
INPUT_TEXT_FILE = "input.txt"  # Path to your text file
OUTPUT_AUDIO_FILE = "output.wav"  # Output audio file name
CHUNK_SIZE = 1800  # Characters per chunk (leaving buffer for safety)

def clean_text_for_tts(text):
    """
    Clean and prepare text for better TTS output
    """
    # Remove or replace problematic characters
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\'\"]', ' ', text)  # Keep basic punctuation
    
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove very long words that might cause issues
    words = text.split()
    cleaned_words = []
    for word in words:
        if len(word) > 50:  # Skip extremely long words
            continue
        cleaned_words.append(word)
    
    text = ' '.join(cleaned_words)
    return text.strip()

def smart_text_splitter(text, chunk_size=1800):
    """
    Split text intelligently at sentence boundaries to avoid cutting words mid-sentence
    """
    # Clean the text first
    text = clean_text_for_tts(text)
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        # Get the chunk
        end_pos = current_pos + chunk_size
        
        if end_pos >= len(text):
            # Last chunk
            chunks.append(text[current_pos:].strip())
            break
        
        # Find the best place to split (sentence boundary)
        chunk_text = text[current_pos:end_pos]
        
        # Look for sentence endings working backwards from the end
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        best_split = -1
        
        for i in range(len(chunk_text)-1, max(len(chunk_text)//2, 0), -1):
            for ending in sentence_endings:
                if chunk_text[i:i+len(ending)] == ending:
                    best_split = i + 1  # Include the period/punctuation
                    break
            if best_split != -1:
                break
        
        if best_split == -1:
            # No sentence boundary found, split at word boundary
            words = chunk_text.split()
            if len(words) > 1:
                # Take all but the last word to avoid cutting mid-word
                chunk_text = ' '.join(words[:-1])
                best_split = len(chunk_text)
            else:
                # Single very long word, just cut it
                best_split = chunk_size
        
        chunks.append(text[current_pos:current_pos + best_split].strip())
        current_pos += best_split
        
        # Skip any whitespace at the beginning of next chunk
        while current_pos < len(text) and text[current_pos].isspace():
            current_pos += 1
    
    return [chunk for chunk in chunks if chunk.strip()]

def convert_large_text_to_speech(api_key, model_id, text_file_path, output_file_path, chunk_size=1800):
    """
    Convert a large text file to speech by splitting it into smart chunks
    """
    try:
        session = Session(api_key)
        
        # Read the entire text file
        with open(text_file_path, 'r', encoding='utf-8') as file:
            full_text = file.read().strip()
        
        if not full_text:
            print("Error: Text file is empty!")
            return False
        
        print(f"📖 Full text length: {len(full_text):,} characters")
        
        # Split text into smart chunks
        chunks = smart_text_splitter(full_text, chunk_size)
        
        print(f"🔄 Split into {len(chunks)} chunks")
        print(f"📊 Average chunk size: {sum(len(chunk) for chunk in chunks) // len(chunks)} characters")
        
        # Process each chunk and combine audio
        audio_chunks = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n🎵 Processing chunk {i}/{len(chunks)} ({len(chunk)} chars)")
            print(f"Preview: {chunk[:100]}...")
            
            try:
                tts_request = TTSRequest(
                    text=chunk,
                    reference_id=model_id
                )
                
                chunk_audio = b''
                for audio_piece in session.tts(tts_request):
                    chunk_audio += audio_piece
                
                audio_chunks.append(chunk_audio)
                print(f"✅ Chunk {i} completed ({len(chunk_audio):,} bytes)")
                
                # Small delay to be nice to the API
                if i < len(chunks):
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing chunk {i}: {str(e)}")
                print("⏩ Skipping this chunk and continuing...")
                continue
        
        # Combine all audio chunks into final file
        print(f"\n🔗 Combining {len(audio_chunks)} audio chunks...")
        
        with open(output_file_path, "wb") as final_audio:
            for audio_chunk in audio_chunks:
                final_audio.write(audio_chunk)
        
        total_size = sum(len(chunk) for chunk in audio_chunks)
        print(f"✅ Large text conversion completed!")
        print(f"📁 Audio saved to: {output_file_path}")
        print(f"📊 Final audio size: {total_size:,} bytes")
        print(f"🎯 Successfully processed {len(audio_chunks)}/{len(chunks)} chunks")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: Text file '{text_file_path}' not found!")
        return False
    except Exception as e:
        print(f"❌ Error during large text conversion: {str(e)}")
        return False

def convert_text_file_to_speech(api_key, model_id, text_file_path, output_file_path):
    """
    Convert a small text file to speech using Fish Audio TTS API
    """
    try:
        session = Session(api_key)
        
        with open(text_file_path, 'r', encoding='utf-8') as file:
            text_content = file.read().strip()
        
        if not text_content:
            print("Error: Text file is empty!")
            return False
        
        # Clean the text
        text_content = clean_text_for_tts(text_content)
        
        print(f"Converting text from '{text_file_path}' to speech...")
        print(f"Text length: {len(text_content)} characters")
        print(f"Using model ID: {model_id}")
        
        tts_request = TTSRequest(
            text=text_content,
            reference_id=model_id
        )
        
        with open(output_file_path, "wb") as audio_file:
            for chunk in session.tts(tts_request):
                audio_file.write(chunk)
        
        print(f"✅ Speech generation completed!")
        print(f"Audio saved to: {output_file_path}")
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: Text file '{text_file_path}' not found!")
        return False
    except Exception as e:
        print(f"❌ Error during speech generation: {str(e)}")
        return False

def main():
    """Main function to run the TTS conversion"""
    
    # Check if configuration is set
    if API_KEY == "your_api_key_here" or MODEL_ID == "your_model_id_here":
        print("⚠️  Please update the configuration section with your actual API key and model ID!")
        return
    
    # Check if input file exists
    if not os.path.exists(INPUT_TEXT_FILE):
        print(f"⚠️  Input file '{INPUT_TEXT_FILE}' not found!")
        print("Please make sure your text file exists and update the INPUT_TEXT_FILE path.")
        return
    
    # Check file size to determine approach
    with open(INPUT_TEXT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    text_length = len(content)
    print(f"📄 Text file size: {text_length:,} characters")
    
    if text_length > 2000:
        print(f"📚 Large file detected! Using smart chunking approach...")
        success = convert_large_text_to_speech(
            api_key=API_KEY,
            model_id=MODEL_ID,
            text_file_path=INPUT_TEXT_FILE,
            output_file_path=OUTPUT_AUDIO_FILE,
            chunk_size=CHUNK_SIZE
        )
    else:
        print(f"📝 Small file, using standard conversion...")
        success = convert_text_file_to_speech(
            api_key=API_KEY,
            model_id=MODEL_ID,
            text_file_path=INPUT_TEXT_FILE,
            output_file_path=OUTPUT_AUDIO_FILE
        )
    
    if success:
        print(f"\n🎉 Your text has been successfully converted to speech!")
        print(f"🎧 You can now play the audio file: {OUTPUT_AUDIO_FILE}")
        print(f"⏱️  For 100K+ characters, this process may take several minutes...")
    else:
        print(f"\n❌ Conversion failed. Check the error messages above.")

if __name__ == "__main__":
    # First, install the required package if not already installed
    try:
        import fish_audio_sdk
    except ImportError:
        print("Installing Fish Audio SDK...")
        os.system("pip install fish-audio-sdk")
        import fish_audio_sdk
    
    main()
