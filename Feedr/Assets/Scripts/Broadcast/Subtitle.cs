
using TMPro;
using UnityEngine;


public class Subtitle : MonoBehaviour
{
    public TextMeshProUGUI subtitleText;
   

    private void Awake()
    {
        ShowController.NewLineContents.AddListener(update_text);
    }

    private void update_text(string t) => subtitleText.text = t;
    
}
