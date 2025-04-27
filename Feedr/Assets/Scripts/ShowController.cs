using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using Unity.VisualScripting;
using UnityEngine;
using UnityEngine.Events;
using Random = UnityEngine.Random;


public class ShowController : MonoBehaviour
{
    private bool isPlaying = false;
    
    public static UnityEvent<string> NewLineContents = new UnityEvent<string>();

    private Segment segment;

    public GameObject characterbase;
    private Dictionary<string, GameObject> characters = new Dictionary<string, GameObject>();
    public List<Transform> spawn_places;

    public TextMeshProUGUI title_text;
    
    private IEnumerator Start()
    {
        yield return new WaitForSeconds(0.5f);
        segment = SegmentLoader.Instance.GetCurrentSegment();
        StartCoroutine(PlaySegment());
        
    }

    IEnumerator PlaySegment()
    {
        if (segment == null)
            yield break;
        title_text.text = segment.title;
        foreach (GameObject character in characters.Values)
        {
            Destroy(character);
        }
        characters.Clear();
        int i = 1;
        foreach (string c in segment.characters)
        {
            Vector3 spawn_pos = spawn_places[i % spawn_places.Count].position;
            i++;
            NewsCharacter newsCharacter = Instantiate(characterbase , spawn_pos , Quaternion.identity).GetComponent<NewsCharacter>();
            newsCharacter.name = c;
            characters.Add(c , newsCharacter.gameObject);
        }

        isPlaying = true;
        Debug.Log($"Playing segment {segment.title}");

        while (segment.HasMoreLines() && isPlaying)
        {
            // Get the next line
            NewsLine newsLine = segment.GetNextLine();

            // Display the text (update your UI here)
            Debug.Log($"{newsLine.character}: {newsLine.text_line}");


            yield return new WaitUntil(() => { return Time.timeScale != 0f; });
            
            NewsCharacter talking = characters[newsLine.character].GetComponent<NewsCharacter>();
            // Play the audio if available
            if (newsLine.voice_line != null)
            {
                talking.audioSource.clip = newsLine.voice_line;
                NewLineContents.Invoke(newsLine.text_line);
                
                talking.audioSource.Play();

                // Wait for the audio to finish
                while (talking.audioSource.isPlaying && isPlaying)
                {
                    yield return null;
                }

                // Small pause between lines
                yield return new WaitForSeconds(0.5f);
            }
            else
            {
                // If no audio, just wait a bit
                yield return new WaitForSeconds(2.0f);
            }
        }

        isPlaying = false;
        Debug.Log("Finished playing segment");
        StartCoroutine(LoadNextSegment());
    }


    public IEnumerator  LoadNextSegment()
    {
        Debug.Log($"Loading segment");
        // Stop current playback
        isPlaying = false;

        yield return StartCoroutine(SegmentLoader.Instance.GetNextSegment());
        
        segment = SegmentLoader.Instance.GetCurrentSegment();
        Debug.Log($"past Loading segment instancer");
        
        if (segment == null)
        {
            Debug.Log("Show Completed");
            yield break;
        }

        
        isPlaying = true;
        StartCoroutine(PlaySegment());
    }
}