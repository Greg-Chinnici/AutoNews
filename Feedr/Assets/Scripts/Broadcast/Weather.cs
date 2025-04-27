using System;
using System.Collections.Generic;
using UnityEngine;
using Random = UnityEngine.Random;


public class Weather : MonoBehaviour, IBroadcastElement
{
    public SpriteRenderer window;
    public List<Sprite> weatherImages = new();

    public bool active { get; set; }

    private void Awake()
    {
        active = false;
        Deactivate();
    }

    public void Activate()
    {
        window.gameObject.SetActive(true);
        if (weatherImages.Count > 0)
        {
            window.sprite = weatherImages[Random.Range(0,
                weatherImages.Count - 1)];
        }
    }

    public void Deactivate()
    {

        window.gameObject.SetActive(false);
    }
}