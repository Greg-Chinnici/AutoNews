using System.Collections.Generic;
using UnityEngine;



    public class Ragdolls : MonoBehaviour , IBroadcastElement
    {
        [HideInInspector] List<GameObject> character_ragdolls = new();
        
        public bool active { get; set; }
        public void Activate()
        {
            // make all the ragdolls and rigid bodies activate
        }

        public void Deactivate()
        {
            throw new System.NotImplementedException();
        }
    }
