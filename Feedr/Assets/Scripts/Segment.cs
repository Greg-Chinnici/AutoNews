using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Segment
{
   public string segmentName;
   public string title;
   public string[] characters;
    
   // The queue of news lines in order
   public Queue<NewsLine> newsLines = new Queue<NewsLine>();
    
    
   public Segment(string name, string title, string[] characters)
   {
      this.segmentName = name;
      this.title = title;
      this.characters = characters;
   }
    
   // Get the next news line
   public NewsLine GetNextLine()
   {
      if (newsLines.Count > 0)
         return newsLines.Dequeue();
      return null;
   }
   public NewsLine PeekNextLine()
   {
      if (newsLines.Count > 0)
         return newsLines.Peek();
      return null;
   }
    
   public bool HasMoreLines()
   {
      return newsLines.Count > 0;
   }
    
   public int GetRemainingLineCount()
   {
      return newsLines.Count;
   }

   
}
