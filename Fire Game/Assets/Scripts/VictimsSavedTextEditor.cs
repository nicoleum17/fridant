using UnityEngine;
using TMPro;
using UnityEditorInternal;

public class VictimsSavedTextEditor : MonoBehaviour
{
    public TextMeshProUGUI savedVictims;
    public void Update()
    {
        if (GameManager.Instance != null && GameManager.Instance.CurrentState != null)
        {
            SimulationState state = GameManager.Instance.CurrentState;
            savedVictims.text = $"Victims Saved: {state.model_data.saved_victims}";
        }

    }

}
