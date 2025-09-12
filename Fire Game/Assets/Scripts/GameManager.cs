using System;
using System.Collections.Generic;
using UnityEngine;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }
    public SimulationState CurrentState { get; private set; }
    public static event Action<SimulationState> OnStateChanged;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
        }
        else
        {
            Instance = this;
        }
    }
    public void UpdateSimulationState(SimulationState newState)
    {
        CurrentState = newState;
        Debug.Log("GameManager: STEP " + newState.model_data.steps);
        OnStateChanged?.Invoke(newState);
    }
}
