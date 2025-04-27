using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public class ShowAdminPanel : MonoBehaviour
{
    public CanvasGroup AdminPanel;
    private bool is_showing = false;

    private void Start()
    {
        HidePanel();
    }
    
    public void TogglePanel()
    {
        is_showing = !is_showing;
        if (is_showing) ShowPanel();
        else HidePanel();
    }

    private void ShowPanel()
    {
        AdminPanel.alpha = 1;
        AdminPanel.interactable = true;
        AdminPanel.blocksRaycasts = true;
    }
    private void HidePanel()
    {
        AdminPanel.alpha = 0;
        AdminPanel.interactable = false;
        AdminPanel.blocksRaycasts = false;
    }
}
