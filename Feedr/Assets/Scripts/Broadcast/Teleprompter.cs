
using System;
using UnityEngine;

public class Teleprompter: MonoBehaviour , IBroadcastElement
{
    
    public bool active { get; set; }
    
    
    private void Start()
    {
        
        active = false;        
        Deactivate();
    }

    public void Activate()
    {
        throw new System.NotImplementedException();
    }

    public void Deactivate()
    {
        throw new System.NotImplementedException();
    }
}
