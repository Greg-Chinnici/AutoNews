
using UnityEngine;

public class NewsLine
{
   public AudioClip voice_line{ private set; get; }
   public string text_line{ private set; get; }
   public string character { private set; get; }

   public NewsLine(AudioClip audioClip, string text, string character_name)
   {
      voice_line = audioClip;
      text_line = text;
      character = character_name;
   }
  
   
}
