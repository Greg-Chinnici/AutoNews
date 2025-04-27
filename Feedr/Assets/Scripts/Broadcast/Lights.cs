using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

public class Lights : MonoBehaviour , IBroadcastElement
{
   public List<Light> lights = new List<Light>();

    public bool active { get; set; }

    public void ToggleLights(Toggle b)
    {
        if (b.value) Activate();
        else Deactivate();
    } 

    public void ToggleLights(UnityEngine.UI.Toggle toggle)
    {
        if (toggle.isOn) Activate();
        else Deactivate();
    }
    public void Activate()
    {
        foreach(Light light in lights)
            light.gameObject.SetActive(true);
    }

    public void Deactivate()
    {
        foreach(Light light in lights)
            light.gameObject.SetActive(false);
    }
}
