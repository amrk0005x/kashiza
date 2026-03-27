import os
import json
import tempfile
import wave
import asyncio
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass
import subprocess

@dataclass
class VoiceConfig:
    wake_word: str = "hey kashiza"
    language: str = "en-US"
    speech_rate: float = 1.0
    voice_id: str = "default"
    silence_threshold: int = 500
    silence_duration: float = 2.0
    max_recording_duration: int = 30

class VoiceInterface:
    def __init__(self, config: VoiceConfig = None):
        self.config = config or VoiceConfig()
        self.is_listening = False
        self.recording_process = None
        self.callbacks: Dict[str, List[Callable]] = {
            'wake_word': [],
            'command': [],
            'error': []
        }
        self.transcription_provider = "whisper"  # or "local"
        self.tts_provider = "local"  # or "elevenlabs"
    
    def on(self, event: str, callback: Callable):
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _emit(self, event: str, data: any):
        for cb in self.callbacks.get(event, []):
            cb(data)
    
    async def start_listening(self):
        self.is_listening = True
        
        while self.is_listening:
            try:
                # Listen for wake word
                audio_file = await self._record_until_silence()
                if not audio_file:
                    continue
                
                # Transcribe
                text = await self._transcribe(audio_file)
                
                if self.config.wake_word.lower() in text.lower():
                    self._emit('wake_word', text)
                    
                    # Listen for command
                    command_audio = await self._record_until_silence()
                    if command_audio:
                        command_text = await self._transcribe(command_audio)
                        self._emit('command', command_text)
                
                os.unlink(audio_file)
                
            except Exception as e:
                self._emit('error', str(e))
    
    def stop_listening(self):
        self.is_listening = False
        if self.recording_process:
            self.recording_process.terminate()
    
    async def _record_until_silence(self) -> Optional[str]:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            output_path = f.name
        
        try:
            # Use sox or arecord for recording
            if os.system("which sox > /dev/null 2>&1") == 0:
                proc = await asyncio.create_subprocess_exec(
                    'sox', '-d', '-b', '16', '-e', 'signed', '-r', '16000', '-c', '1',
                    output_path, 'silence', '1', '0.1', str(self.config.silence_threshold),
                    '1', str(self.config.silence_duration), str(self.config.silence_threshold),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    'arecord', '-f', 'cd', '-t', 'wav', '-d', str(self.config.max_recording_duration),
                    output_path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
            
            self.recording_process = proc
            await asyncio.wait_for(proc.wait(), timeout=self.config.max_recording_duration + 5)
            
            return output_path if os.path.exists(output_path) and os.path.getsize(output_path) > 1000 else None
            
        except asyncio.TimeoutError:
            proc.terminate()
            return None
        except Exception:
            return None
    
    async def _transcribe(self, audio_file: str) -> str:
        if self.transcription_provider == "whisper":
            return await self._transcribe_whisper(audio_file)
        return await self._transcribe_local(audio_file)
    
    async def _transcribe_whisper(self, audio_file: str) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            
            with open(audio_file, 'rb') as f:
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language=self.config.language[:2]
                )
            
            return response.text
        except Exception as e:
            print(f"Whisper error: {e}")
            return ""
    
    async def _transcribe_local(self, audio_file: str) -> str:
        try:
            from faster_whisper import WhisperModel
            
            model = WhisperModel("base", device="cpu")
            segments, _ = model.transcribe(audio_file, language=self.config.language[:2])
            
            return " ".join([s.text for s in segments])
        except Exception as e:
            print(f"Local whisper error: {e}")
            return ""
    
    async def speak(self, text: str) -> bool:
        if self.tts_provider == "elevenlabs":
            return await self._speak_elevenlabs(text)
        return await self._speak_local(text)
    
    async def _speak_local(self, text: str) -> bool:
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                output_path = f.name
            
            # Use espeak or say
            if os.system("which espeak > /dev/null 2>&1") == 0:
                proc = await asyncio.create_subprocess_exec(
                    'espeak', '-w', output_path, text,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()
            elif os.system("which say > /dev/null 2>&1") == 0:
                proc = await asyncio.create_subprocess_exec(
                    'say', '-o', output_path, text,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()
            else:
                return False
            
            # Play audio
            if os.system("which aplay > /dev/null 2>&1") == 0:
                proc = await asyncio.create_subprocess_exec('aplay', output_path)
                await proc.wait()
            elif os.system("which afplay > /dev/null 2>&1") == 0:
                proc = await asyncio.create_subprocess_exec('afplay', output_path)
                await proc.wait()
            
            os.unlink(output_path)
            return True
            
        except Exception as e:
            print(f"TTS error: {e}")
            return False
    
    async def _speak_elevenlabs(self, text: str) -> bool:
        try:
            from elevenlabs import generate, play
            
            audio = generate(text=text, voice=self.config.voice_id)
            play(audio)
            return True
        except Exception as e:
            print(f"ElevenLabs error: {e}")
            return False
    
    def process_voice_command(self, text: str, orchestrator) -> str:
        # Parse voice command and route to appropriate handler
        text_lower = text.lower()
        
        # Code commands
        if any(w in text_lower for w in ["code", "write", "create function"]):
            return f"Creating code for: {text}"
        
        # Search commands
        if any(w in text_lower for w in ["search", "find", "look for"]):
            return f"Searching for: {text}"
        
        # System commands
        if any(w in text_lower for w in ["open", "launch", "start"]):
            return f"Launching: {text}"
        
        # Default: pass to orchestrator
        return text

class VoiceCommandParser:
    COMMANDS = {
        'code': ['code', 'write', 'create', 'implement', 'function', 'class'],
        'search': ['search', 'find', 'look for', 'where is'],
        'run': ['run', 'execute', 'start', 'launch'],
        'explain': ['explain', 'what is', 'how does', 'tell me about'],
        'fix': ['fix', 'debug', 'repair', 'solve'],
        'review': ['review', 'check', 'analyze'],
        'stop': ['stop', 'halt', 'cancel', 'abort']
    }
    
    def parse(self, text: str) -> Dict:
        text_lower = text.lower()
        
        for cmd_type, keywords in self.COMMANDS.items():
            for kw in keywords:
                if kw in text_lower:
                    # Extract argument
                    idx = text_lower.find(kw)
                    arg = text[idx + len(kw):].strip()
                    
                    return {
                        'command_type': cmd_type,
                        'keyword': kw,
                        'argument': arg,
                        'original': text
                    }
        
        return {
            'command_type': 'general',
            'keyword': None,
            'argument': text,
            'original': text
        }
