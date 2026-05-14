import asyncio
import edge_tts

import tempfile
import os
import pygame  # for playback

# en-US-AriaNeural | Female | en-US | Aria (Natural American)
# en-US-JennyNeural | Female | en-US | Jenny (Bright American)
# en-US-GuyNeural | Male | en-US | Guy (Friendly American)
# en-GB-SoniaNeural | Female | en-GB | Sonia (British)
# en-IN-NeerjaNeural | Female | en-IN | Neerja (Indian)
# ur-PK-AsadNeural | Male | ur-PK | Asad (Urdu, Pakistan)
# ur-PK-UzmaNeural | Female | ur-PK | Uzma (Urdu, Pakistan)
# zh-CN-XiaoxiaoNeural | Female | zh-CN | Xiaoxiao (Chinese)
# fr-FR-DeniseNeural | Female | fr-FR | Denise (French)


class NaturalTTS:

    def __init__(self, voice="en-GB-SoniaNeural", rate="+5%", volume="+0%"):
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def _speak_async(self, text):
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume)

        # Save audio to a temporary mp3 file
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_file.close()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                with open(tmp_file.name, "ab") as f:
                    f.write(chunk["data"])

        # print("[TTS] Speech generated, now playing...")

        # Play audio using pygame
        pygame.mixer.init()
        pygame.mixer.music.load(tmp_file.name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        # Cleanup
        pygame.mixer.quit()
        os.remove(tmp_file.name)
        print("[TTS] Playback finished.")

    def say(self, text):
        try:
            asyncio.run(self._speak_async(text))
        except RuntimeError:
            # If already inside an event loop
            asyncio.get_event_loop().create_task(self._speak_async(text))
