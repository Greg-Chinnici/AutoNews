using TMPro;
using UnityEngine;

using Shibuya24.Utility;
using UnityEngine.Serialization;

// 4 Fucking hours of debugging and crashes. this makes it work by
// finding the loader when it somehow keeps removing itself  
// DO NOT TOUCH THIS
public class DragDropTest : MonoBehaviour
{
    public TextMeshProUGUI Status;
    public TextMeshProUGUI folder;
    [SerializeField] private SegmentLoader Loader;

    private void Awake()
    {
        if (Loader == null)
        {
            // Try to find one automatically
            Loader = GetComponent<SegmentLoader>();
            if (Loader == null)
            {
                Debug.LogError("Loader missing on DragDropTest!");
            }
        }
    }

    private void Start()
    {
        // Hook up the Drag and Drop system
        UniDragAndDrop.onDragAndDropFilePath = HandleDragAndDrop;
        UniDragAndDrop.Initialize();

        Status.text = $"Latest path {checkForRecentPath()}";
    }

    private void HandleDragAndDrop(string path)
    {
        Debug.Log($"Drag and Drop detected: {path}");

        // Double-check: if Loader somehow became null, try to find it again
        if (Loader == null)
        {
            Debug.LogWarning("Loader was null at drag time. Attempting to find a SegmentLoader...");
            Loader = FindObjectOfType<SegmentLoader>(); // slower but safe for now
        }

        if (Loader == null)
        {
            Debug.LogError("No SegmentLoader found in scene!");
            return;
        }

        
        Status.text = path;
        Loader.SetBasePath(path);
        saveRecentPath(path);
        BeginLoading();
        Debug.Log($"Started loading segment from folder drag and drop at: {path}");
    }

    public void BeginLoading()
    {
        if (Loader == null)
        {
            Debug.LogWarning("Loader was null at drag time. Attempting to find a SegmentLoader...");
            Loader = FindObjectOfType<SegmentLoader>(); // slower but safe for now
        }
        
        StartCoroutine(Loader.GetNextSegment());
    }


    private string checkForRecentPath()
    {
        string n = PlayerPrefs.GetString("RecentPath", "not found");
        if (n != "not found")
        {
            SegmentLoader.Instance.SetBasePath(n);
            folder.text = $"Looking at folder at {n}";
            BeginLoading();
        }
           
        return n;
    }

    private void saveRecentPath(string path)
    {
        PlayerPrefs.SetString("RecentPath", path);
    }
}
