using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Jukebox : MonoBehaviour
{
    public List<AudioClip> audioClips = new List<AudioClip>();
    public AudioSource jukebox;
    public TMPro.TextMeshProUGUI jukeboxText;
    
    private Coroutine song_playing;
    private int current_song_index = 0;

    private bool paused = false;

    private void Start()
    {
        SkipSong();
        PausePlay();
    }

    public void ChangeVolume(float volume) => jukebox.volume = volume;

    public void PausePlay()
    {
        if (jukebox.clip == null)
        {
            SkipSong();
            return;
        }
        
        if (jukebox.isPlaying)
        {
            jukebox.Pause();
            paused = true;
        }
        else
        {
            jukebox.UnPause();
            paused = false;
        }
    }

    private void new_song(AudioClip song)
    {
        if (song_playing != null)
            StopCoroutine(song_playing);

        jukebox.clip = song;
        jukebox.Play();
        jukeboxText.text = jukebox.clip.name;
        song_playing = StartCoroutine(playing());
    }

    public void SkipSong()
    {
        current_song_index++;
        current_song_index %= audioClips.Count;
        
        if (song_playing != null)
            StopCoroutine(song_playing);
        
        new_song(audioClips[current_song_index]);
    }

    IEnumerator playing()
    {
        yield return new WaitUntil(() => jukebox.isPlaying);

        yield return new WaitForSeconds(jukebox.clip.length);

        if (paused) 
            yield break;
            
        current_song_index = (current_song_index + 1) % audioClips.Count;
        new_song(audioClips[current_song_index]);
    }

}
