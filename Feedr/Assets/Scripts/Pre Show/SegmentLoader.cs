using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.Networking;

public class SegmentLoader : MonoBehaviour
{
    [Serializable]
    public class DialogueLine
    {
        public string character;
        public string line;
    }

    [Serializable]
    public class SegmentMetadata
    {
        public string mainTitle;
        public string[] characters;
        public DialogueLine[] dialogue;
    }

    [SerializeField] private string absoluteBasePath;

    private Segment currentSegment;
    
    public UnityEvent SegmentLoaded;
    public UnityEvent SegmentFailed;

    private Queue<string> child_segments = new();

    public static SegmentLoader Instance { get; private set; }
    private void Start()
    {
        if (Instance == null)
            Instance = this;
        else
            Destroy(gameObject);
        
        DontDestroyOnLoad(gameObject);
        
        Application.runInBackground = true;
        
        
    }

    public void SetBasePath(string path)
    {
        child_segments.Clear();
        absoluteBasePath = path;
        Debug.Log($"Set absolute base path: {absoluteBasePath}");
        
        string[] folders = Directory.GetDirectories(absoluteBasePath);
        Debug.Log($"folder count: {folders.Length}");
        foreach (string folder in folders)
            child_segments.Enqueue(folder);
        
    }

    public IEnumerator GetNextSegment()
    {
        UnloadCurrentSegment();
        
        string child_name = child_segments.Dequeue();
        if (string.IsNullOrEmpty(child_name))
        {
            currentSegment = null;
            yield break;
        }
        
        yield return StartCoroutine(LoadSegment(child_name));
    }
    // Load a segment from a folder using absolute path
    private IEnumerator LoadSegment(string absoulutePathToSegment)
    {
        if (string.IsNullOrEmpty(absoluteBasePath) || !Directory.Exists(absoluteBasePath))
        {
            Debug.LogError("Invalid absolute base path: " + absoluteBasePath);
            SegmentFailed?.Invoke();
            yield break;
        }

        string segmentName = absoulutePathToSegment.Substring(absoulutePathToSegment.LastIndexOf("/"));
        Debug.Log($"Loading segment: {segmentName} from path: {absoluteBasePath}");

        // Unload any previous segment
        UnloadCurrentSegment();

        // Build the absolute path to the segment folder
        string segmentPath = absoulutePathToSegment;

        if (!Directory.Exists(segmentPath))
        {
            Debug.LogError($"Segment directory does not exist: {segmentPath}");
            SegmentFailed?.Invoke();
            yield break;
        }

        // Load metadata.json
        string metadataPath = Path.Combine(segmentPath,
            "metadata.json");
        if (!File.Exists(metadataPath))
        {
            Debug.LogError($"Metadata file not found: {metadataPath}");
            SegmentFailed?.Invoke();
            yield break;
        }

        // Read and parse metadata
        string metadataText = File.ReadAllText(metadataPath);
        Debug.Log($"Metadata content: {metadataText}");
        SegmentMetadata metadata = JsonUtility.FromJson<SegmentMetadata>(metadataText);

        // Create segment object
        currentSegment = new Segment(
            segmentName,
            metadata.mainTitle,
            metadata.characters
        );

        Debug.Log($"Loaded segment: {metadata.mainTitle} with {metadata.characters.Length} characters");

      
        // Dictionary to store loaded audio clips
        Dictionary<string, AudioClip> audioClips = new Dictionary<string, AudioClip>();

        // Audio folder path
        string audioFolderPath = Path.Combine(segmentPath, "audio");

        // Preload all audio files
        int lineNumber = 0;
        foreach (DialogueLine dialogueLine in metadata.dialogue)
        {
            lineNumber++;
            string character = dialogueLine.character;
            string text = dialogueLine.line;

            string audioKeyBase = $"{lineNumber}_{character}";

            AudioClip audioClip = null;
            bool found = false;

            foreach (string ext in new[] { ".mp3", ".wav" })
            {
                string audioPath = Path.Combine(audioFolderPath, $"{audioKeyBase}{ext}");

                if (File.Exists(audioPath))
                {
                    using (UnityWebRequest audioRequest = UnityWebRequestMultimedia.GetAudioClip("file://" + audioPath, GetAudioType(ext)))
                    {
                        yield return audioRequest.SendWebRequest();

                        if (audioRequest.result == UnityWebRequest.Result.Success)
                        {
                            audioClip = DownloadHandlerAudioClip.GetContent(audioRequest);
                            found = true;
                            Debug.Log($"Loaded audio: {audioKeyBase} from {audioPath}");
                            break;
                        }
                        else
                        {
                            Debug.LogWarning($"Failed to load audio file {audioPath}: {audioRequest.error}");
                        }
                    }
                }
            }

            if (!found)
            {
                Debug.LogWarning($"Audio not found for {audioKeyBase}");
            }

            NewsLine newsLine = new NewsLine(audioClip, text, character);
            currentSegment.newsLines.Enqueue(newsLine);
            
            if (text != null) 
                Debug.Log($"Enqueued line: {character}_{lineNumber}: \"{text.Substring(0, Mathf.Min(20, text.Length))}...\"");

            yield return null; // wait a frame between loads so it wont crash
            
        }
        Debug.Log($"Successfully loaded segment: {segmentName} with {currentSegment.GetRemainingLineCount()} lines");

        SegmentLoaded?.Invoke();
    }

    // Helper method to determine AudioType from file extension
    private AudioType GetAudioType(string extension)
    {
        switch (extension.ToLower())
        {
            case ".mp3":
                return AudioType.MPEG;
            case ".ogg":
                return AudioType.OGGVORBIS;
            case ".wav":
                return AudioType.WAV;
            default:
                return AudioType.UNKNOWN;
        }
    }

    // Unload the current segment
    public void UnloadCurrentSegment()
    { 
        currentSegment = null;
    }

    // Get the current segment
    public Segment GetCurrentSegment()
    {
        return currentSegment;
    }
}