import os
import pyglet


def load_lofi_audio(audio_path):
    """
    Load Lo-Fi audio file with graceful degradation.

    Returns a pyglet.media.Player with the audio queued and looping,
    or None if the file is missing or corrupt.

    Parameters
    ----------
    audio_path : str
        Path to the audio file (e.g. ``assets/audio/lofi.mp3``).
    """
    if not os.path.exists(audio_path):
        print(f"[audio] WARNING: audio file not found at {audio_path}")
        print("[audio] Scene will run without music.")
        return None

    try:
        source = pyglet.media.load(audio_path)
        player = pyglet.media.Player()
        player.queue(source)
        player.loop = True
        player.play()
        print(f"[audio] Lo-Fi track loaded and playing: {audio_path}")
        return player
    except Exception as e:
        print(f"[audio] WARNING: failed to load audio ({e})")
        print("[audio] Scene will run without music.")
        return None


def toggle_audio(player):
    """
    Pause or resume audio playback.

    Parameters
    ----------
    player : pyglet.media.Player or None
        The audio player to toggle. Safe to pass None.
    """
    if player is None:
        return
    if player.playing:
        player.pause()
    else:
        player.play()
