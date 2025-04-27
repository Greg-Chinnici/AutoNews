using System;
using UnityEngine;

public class NewsCharacter : MonoBehaviour
{
    public string name = "";
    
    public Transform headTransform; // Drag the head bone here
    public float bounceMultiplier = 0.3f; // Increased for more dramatic movement
    public float maxBounce = 0.5f; // Increased for higher max movement
    public float smoothing = 0.05f; // How smooth it returns
    
    [Header("Enhanced Movement")]
    public bool useExaggeratedMovement = true;
    public float volumeThreshold = 0.4f; // Threshold for extra movement
    public float exaggerationMultiplier = 1.8f; // Extra bounce for louder sounds
    public float returnSpeed = 3.0f; // How quickly head returns to normal when volume drops
    
    [Header("Rotation Settings")]
    public float rotationAmount = 5.0f; // Degrees to rotate (positive = forward tilt)
    public float rotationSmoothness = 0.1f; // How smooth the rotation is
    
    public AudioSource audioSource;
    private Vector3 initialLocalPos;
    private Quaternion initialLocalRot;
    private float currentBounce = 0f;
    private float bounceVelocity = 0f;
    private float lastVolume = 0f;
    private float currentRotation = 0f;
    private float rotationVelocity = 0f;

    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        if (headTransform == null)
        {
            Debug.LogError("Head transform not assigned on " + gameObject.name);
            return;
        }
        initialLocalPos = headTransform.localPosition;
        initialLocalRot = headTransform.localRotation;
    }

    void Update()
    {
        float[] spectrum = new float[64]; // Increased from 32 for better frequency range
        audioSource.GetSpectrumData(spectrum, 0, FFTWindow.Blackman); // Changed window type for better results
        
        float volume = 0f;
        // Focus on vocal frequencies (mid-range)
        for (int i = 4; i < spectrum.Length; i++)
        {
            // Weight mid frequencies higher
            float weight = (i < 16) ? 1.5f : 1.0f;
            volume += spectrum[i] * weight;
        }
        
        volume = Mathf.Clamp01(volume * 15f); // Boosted more
        
        float targetBounce = volume * bounceMultiplier;
        
        // Add dramatic effect for louder sounds
        if (useExaggeratedMovement && volume > volumeThreshold)
        {
            // Calculate how much above threshold we are
            float excessVolume = volume - volumeThreshold;
            // Add extra bounce based on how much we exceeded threshold
            targetBounce += excessVolume * exaggerationMultiplier;
        }
        
        // Apply max limit
        targetBounce = Mathf.Min(targetBounce, maxBounce);
        
        // Adjust smoothing based on whether we're going up or down
        float currentSmoothing = smoothing;
        if (volume < lastVolume)
        {
            // Faster return when volume drops
            currentSmoothing = smoothing / returnSpeed;
        }
        
        // Smooth bounce amount
        currentBounce = Mathf.SmoothDamp(currentBounce, targetBounce, ref bounceVelocity, currentSmoothing, Mathf.Infinity, Time.deltaTime);
        
        // Calculate rotation - scale rotation with bounce amount
        float targetRotation = (currentBounce / maxBounce) * rotationAmount;
        currentRotation = Mathf.SmoothDamp(currentRotation, targetRotation, ref rotationVelocity, rotationSmoothness, Mathf.Infinity, Time.deltaTime);
        
        // Apply position change
        headTransform.localPosition = initialLocalPos + headTransform.localRotation * (Vector3.up * currentBounce);
        
        // Apply rotation change - rotate around local X axis (tilting forward/backward)
        headTransform.localRotation = initialLocalRot * Quaternion.Euler(currentRotation, 0, 0);
        
        // Store current volume for next frame
        lastVolume = volume;
    }

    private void OnDestroy()
    {
        if (audioSource != null)
        {
            audioSource.Stop();
        }
        
        // Reset head position and rotation when destroyed
        if (headTransform != null)
        {
            headTransform.localPosition = initialLocalPos;
            headTransform.localRotation = initialLocalRot;
        }
    }
}