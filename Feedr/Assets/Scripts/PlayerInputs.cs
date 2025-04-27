using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;
public class PlayerInputs : MonoBehaviour
{

    public KeyCode ToggleAdmin;
    public UnityEvent OnToggleAdmin;
    private void Update()
    {
        if (Input.GetKeyDown(ToggleAdmin)) OnToggleAdmin.Invoke();
        
    }
}
